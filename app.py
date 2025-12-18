import json
import os
from datetime import datetime
from io import BytesIO

import openpyxl
import streamlit as st
from fpdf import FPDF

# ファイルパス
JSON_FILE = "data.json"
IMAGES_DIR = "images"
TEMPLATE_FILE = "templates/inspection_template.xlsx"


def ensure_directories():
    """必要なディレクトリを作成する"""
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)


def load_parts_data():
    """JSONファイルから部品データを読み込む"""
    if not os.path.exists(JSON_FILE):
        return []

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("parts", [])


def save_parts_data(parts):
    """部品データをJSONファイルに保存する"""
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump({"parts": parts}, f, ensure_ascii=False, indent=2)


def save_part(part_data, image_file=None):
    """新しい部品を追加する（画像があれば保存）"""
    parts = load_parts_data()

    # 画像を保存
    if image_file is not None:
        ext = os.path.splitext(image_file.name)[1]
        image_filename = f"{part_data['id']}{ext}"
        image_path = os.path.join(IMAGES_DIR, image_filename)

        with open(image_path, "wb") as f:
            f.write(image_file.getbuffer())

        part_data["image_file"] = image_filename
    else:
        part_data["image_file"] = None

    parts.append(part_data)
    save_parts_data(parts)


def get_image_path(part):
    """部品の画像パスを取得する（存在する場合）"""
    if part.get("image_file"):
        path = os.path.join(IMAGES_DIR, part["image_file"])
        if os.path.exists(path):
            return path
    return None


def load_inspection_template():
    """Excelテンプレートから検査項目を読み込む"""
    if not os.path.exists(TEMPLATE_FILE):
        # デフォルトの検査項目
        return [
            {"no": 1, "item": "外観検査", "criteria": "傷・変形・錆なきこと"},
            {"no": 2, "item": "寸法検査（長さ）", "criteria": "100±0.5mm"},
            {"no": 3, "item": "寸法検査（幅）", "criteria": "50±0.3mm"},
            {"no": 4, "item": "寸法検査（厚さ）", "criteria": "10±0.1mm"},
            {"no": 5, "item": "硬度検査", "criteria": "HRC 58-62"},
            {"no": 6, "item": "動作確認", "criteria": "スムーズに動作すること"},
        ]

    wb = openpyxl.load_workbook(TEMPLATE_FILE)
    ws = wb.active

    items = []
    for row in range(6, 12):  # 6行目から11行目まで（6項目）
        no = ws.cell(row=row, column=1).value
        item = ws.cell(row=row, column=2).value
        criteria = ws.cell(row=row, column=3).value
        if no and item:
            items.append({"no": no, "item": item, "criteria": criteria or ""})

    return items


def auto_judge(item_no, result, criteria):
    """測定値から自動判定を行う"""
    if not result:
        return ""

    result = result.strip()

    # 項目1, 6は「OK」で合格
    if item_no in [1, 6]:
        if result.upper() == "OK":
            return "合格"
        elif result.upper() == "NG":
            return "不合格"
        return ""

    # 項目2-5は数値判定（範囲チェック）
    # 判定基準のパターン: "100±0.5mm", "HRC 58-62"
    try:
        # 測定値を数値に変換
        result_value = float(result.replace(",", "."))

        # ±形式の判定基準をパース（例: "100±0.5mm"）
        if "±" in criteria:
            import re
            match = re.search(r"([\d.]+)±([\d.]+)", criteria)
            if match:
                base = float(match.group(1))
                tolerance = float(match.group(2))
                if base - tolerance <= result_value <= base + tolerance:
                    return "合格"
                else:
                    return "不合格"

        # 範囲形式の判定基準をパース（例: "HRC 58-62"）
        if "-" in criteria:
            import re
            match = re.search(r"([\d.]+)-([\d.]+)", criteria)
            if match:
                min_val = float(match.group(1))
                max_val = float(match.group(2))
                if min_val <= result_value <= max_val:
                    return "合格"
                else:
                    return "不合格"

    except (ValueError, AttributeError):
        pass

    return ""


class JapanesePDF(FPDF):
    """日本語対応PDF"""

    def __init__(self):
        super().__init__()
        # 日本語フォントを追加
        font_path = "fonts/NotoSansJP-Regular.ttf"
        if os.path.exists(font_path):
            self.add_font("NotoSansJP", "", font_path)
            self.font_name = "NotoSansJP"
        else:
            self.font_name = "Helvetica"

    def header(self):
        self.set_font(self.font_name, "", 16)
        if self.font_name == "NotoSansJP":
            self.cell(0, 10, "部品検査表", align="C", new_x="LMARGIN", new_y="NEXT")
        else:
            self.cell(
                0, 10, "Inspection Report", align="C", new_x="LMARGIN", new_y="NEXT"
            )
        self.ln(5)


def generate_pdf(inspection_data, part_data):
    """検査結果をPDFに出力する"""
    pdf = JapanesePDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # 基本情報
    pdf.set_font(pdf.font_name, "", 10)

    pdf.cell(30, 8, "検査日:", border=1)
    pdf.cell(50, 8, inspection_data.get("date", ""), border=1)
    pdf.cell(30, 8, "検査者:", border=1)
    pdf.cell(50, 8, inspection_data.get("inspector", ""), border=1)
    pdf.ln()

    pdf.cell(30, 8, "部品ID:", border=1)
    pdf.cell(50, 8, part_data.get("id", ""), border=1)
    pdf.cell(30, 8, "部品名:", border=1)
    pdf.cell(50, 8, part_data.get("name", ""), border=1)
    pdf.ln()
    pdf.ln(5)

    # 検査項目テーブルヘッダー
    pdf.set_fill_color(68, 114, 196)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(10, 8, "No.", border=1, fill=True, align="C")
    pdf.cell(40, 8, "検査項目", border=1, fill=True, align="C")
    pdf.cell(45, 8, "判定基準", border=1, fill=True, align="C")
    pdf.cell(35, 8, "測定値/結果", border=1, fill=True, align="C")
    pdf.cell(20, 8, "判定", border=1, fill=True, align="C")
    pdf.cell(40, 8, "備考", border=1, fill=True, align="C")
    pdf.ln()

    # 検査項目データ
    pdf.set_text_color(0, 0, 0)
    for item in inspection_data.get("items", []):
        pdf.cell(10, 8, str(item.get("no", "")), border=1, align="C")
        pdf.cell(40, 8, item.get("item", "")[:15], border=1)
        pdf.cell(45, 8, item.get("criteria", "")[:18], border=1)
        pdf.cell(35, 8, item.get("result", ""), border=1, align="C")
        pdf.cell(20, 8, item.get("judgment", ""), border=1, align="C")
        pdf.cell(40, 8, item.get("note", "")[:15], border=1)
        pdf.ln()

    # 総合判定
    pdf.ln(5)
    pdf.set_fill_color(217, 226, 243)
    pdf.cell(40, 10, "総合判定:", border=1, fill=True, align="C")
    overall = inspection_data.get("overall_judgment", "")
    if overall == "合格":
        pdf.set_text_color(0, 128, 0)
    elif overall == "不合格":
        pdf.set_text_color(255, 0, 0)
    pdf.cell(60, 10, overall, border=1, align="C")
    pdf.set_text_color(0, 0, 0)

    return bytes(pdf.output())


# ディレクトリ作成
ensure_directories()

# ページ設定
st.set_page_config(
    page_title="部品検査箇所表示",
    page_icon="🔍",
    layout="wide"
)

# データ読み込み
parts_data = load_parts_data()

# カテゴリ一覧を取得
if parts_data:
    categories = ["すべて"] + sorted(
        list(set(part["category"] for part in parts_data))
    )
else:
    categories = ["すべて"]

# セッション状態の初期化
if "selected_part" not in st.session_state:
    st.session_state.selected_part = None
if "show_add_form" not in st.session_state:
    st.session_state.show_add_form = False
if "show_inspection_form" not in st.session_state:
    st.session_state.show_inspection_form = False
if "inspection_results" not in st.session_state:
    st.session_state.inspection_results = {}

# サイドバー（検索・フィルタ）
st.sidebar.title("🔍 検索・フィルタ")
search_query = st.sidebar.text_input(
    "部品名・IDで検索", placeholder="例: ボルト, BLT-001"
)
selected_category = st.sidebar.selectbox("カテゴリで絞り込み", categories)

# フィルタリング処理
filtered_parts = parts_data.copy()

if search_query:
    filtered_parts = [
        part for part in filtered_parts
        if search_query.lower() in part["name"].lower()
        or search_query.lower() in part["id"].lower()
    ]

if selected_category != "すべて":
    filtered_parts = [
        part for part in filtered_parts
        if part["category"] == selected_category
    ]

# サイドバーに検索結果数を表示
st.sidebar.markdown("---")
st.sidebar.info(f"該当部品: {len(filtered_parts)} 件")

# 部品追加ボタン
st.sidebar.markdown("---")
if st.sidebar.button("➕ 新規部品を追加", width="stretch"):
    st.session_state.show_add_form = not st.session_state.show_add_form
    st.session_state.show_inspection_form = False

# 検査表ボタン
if st.sidebar.button("📋 検査表を作成", width="stretch"):
    st.session_state.show_inspection_form = not st.session_state.show_inspection_form
    st.session_state.show_add_form = False

# メインエリア
st.title("🔍 部品検査箇所表示システム")
st.markdown("検査する部品を選択して、検査項目・注意点・保管場所を確認できます。")
st.markdown("---")

# 部品追加フォーム
if st.session_state.show_add_form:
    st.subheader("➕ 新規部品登録")

    with st.form("add_part_form"):
        col1, col2 = st.columns(2)

        with col1:
            new_id = st.text_input("部品ID *", placeholder="例: BLT-002")
            new_name = st.text_input("部品名 *", placeholder="例: 六角ボルト M12")
            new_category = st.text_input("カテゴリ *", placeholder="例: 締結部品")
            new_storage = st.text_input(
                "保管場所 *", placeholder="例: A棟-1F-棚番号A-15"
            )

        with col2:
            new_inspection = st.text_area(
                "検査項目 *（1行に1項目）",
                placeholder="ねじ山の損傷確認\n頭部の変形確認\n表面の錆確認",
                height=100
            )
            new_cautions = st.text_area(
                "注意点（1行に1項目）",
                placeholder="トルク管理が重要\n再使用回数に注意",
                height=100
            )
            new_image_desc = st.text_input(
                "検査箇所イメージの説明",
                placeholder="例: ボルト頭部・ねじ山部の検査ポイント"
            )

        # 画像アップロード
        uploaded_image = st.file_uploader(
            "検査箇所の画像（任意）",
            type=["png", "jpg", "jpeg"],
            help="PNG, JPG, JPEG形式の画像をアップロードできます"
        )

        submitted = st.form_submit_button("登録", width="stretch")

        if submitted:
            # バリデーション
            if not new_id or not new_name or not new_category or not new_storage:
                st.error("必須項目（*）を入力してください。")
            elif any(part["id"] == new_id for part in parts_data):
                st.error(f"部品ID '{new_id}' は既に存在します。")
            elif not new_inspection.strip():
                st.error("検査項目を1つ以上入力してください。")
            else:
                # 新規部品データを作成
                new_part = {
                    "id": new_id,
                    "name": new_name,
                    "category": new_category,
                    "inspection_items": [
                        item.strip() for item in new_inspection.split("\n")
                        if item.strip()
                    ],
                    "cautions": [
                        item.strip() for item in new_cautions.split("\n")
                        if item.strip()
                    ] if new_cautions.strip() else ["特になし"],
                    "storage": new_storage,
                    "image_description": (
                        new_image_desc if new_image_desc else "検査箇所"
                    )
                }

                # JSONに保存（画像も含む）
                save_part(new_part, uploaded_image)
                st.success(f"部品 '{new_name}' を登録しました！")
                st.session_state.show_add_form = False
                st.rerun()

    st.markdown("---")

# 検査表フォーム
if st.session_state.show_inspection_form:
    st.subheader("📋 検査表入力")

    # 検査項目をテンプレートから読み込み
    inspection_items = load_inspection_template()

    # 基本情報入力
    info_col1, info_col2, info_col3 = st.columns(3)
    with info_col1:
        inspection_date = st.date_input("検査日", value=datetime.now())
    with info_col2:
        inspector_name = st.text_input("検査者名", placeholder="山田太郎")
    with info_col3:
        # 部品選択
        part_options = ["選択してください"] + [
            f"{p['id']} - {p['name']}" for p in parts_data
        ]
        selected_part_for_inspection = st.selectbox(
            "対象部品", part_options
        )

    # 選択された部品の情報を取得
    selected_part_info = None
    if selected_part_for_inspection != "選択してください":
        part_id = selected_part_for_inspection.split(" - ")[0]
        selected_part_info = next(
            (p for p in parts_data if p["id"] == part_id), None
        )

    st.markdown("---")

    # 2カラムレイアウト：左に部品情報、右に検査入力
    left_col, right_col = st.columns([1, 2])

    # 左カラム：部品情報（固定表示）
    with left_col:
        st.markdown("### 📌 部品情報")

        if selected_part_info:
            st.markdown(f"**{selected_part_info['name']}**")
            st.caption(f"ID: {selected_part_info['id']}")

            # 検査箇所画像
            image_path = get_image_path(selected_part_info)
            if image_path:
                st.image(image_path, caption="検査箇所", width="stretch")
            else:
                st.markdown(
                    f"""
                    <div style="
                        background-color: #f0f0f0;
                        border: 1px dashed #ccc;
                        border-radius: 5px;
                        padding: 20px;
                        text-align: center;
                        color: #666;
                        font-size: 12px;
                    ">
                        🔍 {selected_part_info.get(
                            'image_description', '検査箇所'
                        )}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # 検査項目
            st.markdown("#### ✅ 検査項目")
            for item in selected_part_info.get("inspection_items", []):
                st.markdown(f"- {item}")

            # 注意点
            st.markdown("#### ⚠️ 注意点")
            for caution in selected_part_info.get("cautions", []):
                st.warning(caution)

            # 保管場所
            st.markdown(f"**📍 保管場所:** {selected_part_info['storage']}")
        else:
            st.info("👆 対象部品を選択すると、検査項目と注意点が表示されます")

    # 右カラム：検査入力フォーム
    with right_col:
        st.markdown("### 📝 測定値入力")
        st.caption(
            "💡 項目1,6は「OK」または「NG」を入力、"
            "項目2-5は数値を入力すると自動判定されます"
        )

        # 検査項目の入力フォーム
        results = []
        all_judgments = []

        for item in inspection_items:
            st.markdown(f"**{item['no']}. {item['item']}**")
            st.caption(f"判定基準: {item['criteria']}")

            col1, col2, col3 = st.columns([2, 1, 2])

            with col1:
                result = st.text_input(
                    "測定値/結果",
                    key=f"result_{item['no']}",
                    placeholder="OK/NG または 数値を入力"
                )

            # 自動判定
            auto_judgment = auto_judge(item["no"], result, item["criteria"])

            with col2:
                if auto_judgment:
                    # 自動判定結果を表示
                    if auto_judgment == "合格":
                        st.success(f"判定: {auto_judgment}")
                    else:
                        st.error(f"判定: {auto_judgment}")
                    judgment = auto_judgment
                else:
                    # 手動選択
                    judgment = st.selectbox(
                        "判定",
                        ["", "合格", "不合格"],
                        key=f"judgment_{item['no']}"
                    )

            with col3:
                note = st.text_input(
                    "備考",
                    key=f"note_{item['no']}",
                    placeholder="備考（任意）"
                )

            results.append({
                "no": item["no"],
                "item": item["item"],
                "criteria": item["criteria"],
                "result": result,
                "judgment": judgment,
                "note": note
            })

            if judgment:
                all_judgments.append(judgment)

            st.markdown("---")

    # 総合判定（自動計算）
    st.markdown("### 総合判定")

    # 全ての項目が判定済みかチェック
    all_items_judged = len(all_judgments) == len(inspection_items)

    if all_items_judged:
        # 一つでも不合格があれば総合不合格
        if "不合格" in all_judgments:
            overall_judgment = "不合格"
            st.error(f"🔴 総合判定: **{overall_judgment}**（不合格項目があります）")
        else:
            overall_judgment = "合格"
            st.success(f"🟢 総合判定: **{overall_judgment}**（全項目合格）")
    else:
        overall_judgment = ""
        st.warning("⚠️ 全ての検査項目を入力すると総合判定が表示されます")

    # 入力状況の表示
    filled_count = len(all_judgments)
    total_count = len(inspection_items)

    # PDF出力ボタン
    st.markdown("---")

    # 部品データを取得
    selected_part_data = None
    if selected_part_for_inspection != "選択してください":
        part_id = selected_part_for_inspection.split(" - ")[0]
        selected_part_data = next(
            (p for p in parts_data if p["id"] == part_id), None
        )

    # 全項目入力済み、かつ全て合格の場合のみボタンを有効化
    has_failure = "不合格" in all_judgments
    button_disabled = not (
        all_items_judged
        and overall_judgment == "合格"
        and inspector_name
        and selected_part_for_inspection != "選択してください"
    )

    if has_failure:
        st.error(
            "🚫 不合格項目があるためPDF出力できません。"
            "全ての項目を合格にしてください。"
        )
    elif button_disabled:
        st.info(
            "📝 全ての項目（検査日、検査者、対象部品、各検査項目）を"
            "入力し、全て合格するとPDF出力ボタンが有効になります。"
        )

    if st.button(
        "📄 PDFで出力",
        width="stretch",
        disabled=button_disabled
    ):
        # 検査データを作成
        inspection_data = {
            "date": inspection_date.strftime("%Y-%m-%d"),
            "inspector": inspector_name,
            "items": results,
            "overall_judgment": overall_judgment
        }

        # PDF生成
        pdf_bytes = generate_pdf(inspection_data, selected_part_data or {})

        # ダウンロードボタン
        st.download_button(
            label="📥 PDFをダウンロード",
            data=pdf_bytes,
            file_name=f"inspection_{selected_part_data['id']}_{inspection_date.strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            type="primary"
        )

        st.success("✅ PDF出力の準備ができました！上のボタンからダウンロードしてください。")

    st.markdown("---")

# 部品カード一覧
st.subheader("📋 部品一覧")

if not filtered_parts:
    st.warning("該当する部品が見つかりません。検索条件を変更してください。")
else:
    # 3列のグリッドレイアウト
    cols = st.columns(3)

    for idx, part in enumerate(filtered_parts):
        col_idx = idx % 3
        with cols[col_idx]:
            # カードのスタイル
            is_selected = st.session_state.selected_part == part["id"]
            border_color = "#1E88E5" if is_selected else "#ddd"
            bg_color = "#E3F2FD" if is_selected else "#fff"

            st.markdown(
                f"""
                <div style="
                    background-color: {bg_color};
                    border: 2px solid {border_color};
                    border-radius: 10px;
                    padding: 15px;
                    margin-bottom: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                ">
                    <div style="font-size: 12px; color: #666;">{part['id']}</div>
                    <div style="font-size: 18px; font-weight: bold; margin: 5px 0;">
                        {part['name']}
                    </div>
                    <div style="
                        display: inline-block;
                        background-color: #E8F5E9;
                        color: #2E7D32;
                        padding: 3px 10px;
                        border-radius: 15px;
                        font-size: 12px;
                    ">{part['category']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button("選択", key=f"btn_{part['id']}", width="stretch"):
                st.session_state.selected_part = part["id"]
                st.rerun()

# 部品詳細表示
st.markdown("---")
st.subheader("📝 部品詳細")

if st.session_state.selected_part:
    # 選択された部品を取得
    selected_part_data = next(
        (part for part in parts_data
         if part["id"] == st.session_state.selected_part),
        None
    )

    if selected_part_data:
        # 2列レイアウトで詳細表示
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown(f"### {selected_part_data['name']}")
            st.markdown(f"**部品番号:** {selected_part_data['id']}")
            st.markdown(f"**カテゴリ:** {selected_part_data['category']}")
            st.markdown(f"**保管場所:** 📍 {selected_part_data['storage']}")

            # 検査項目
            st.markdown("#### ✅ 検査項目")
            for item in selected_part_data["inspection_items"]:
                st.markdown(f"- {item}")

            # 注意点
            st.markdown("#### ⚠️ 注意点")
            for caution in selected_part_data["cautions"]:
                st.warning(caution)

        with col2:
            # 検査箇所画像
            st.markdown("#### 🖼️ 検査箇所イメージ")

            image_path = get_image_path(selected_part_data)
            if image_path:
                # 画像がある場合は表示
                st.image(
                    image_path,
                    caption=selected_part_data.get(
                        "image_description", "検査箇所"
                    ),
                    width="stretch"
                )
            else:
                # プレースホルダー表示
                st.markdown(
                    f"""
                    <div style="
                        background-color: #f5f5f5;
                        border: 2px dashed #ccc;
                        border-radius: 10px;
                        padding: 60px 20px;
                        text-align: center;
                        color: #666;
                    ">
                        <div style="font-size: 48px;">🔍</div>
                        <div style="margin-top: 10px; font-weight: bold;">
                            {selected_part_data.get(
                                'image_description', '検査箇所'
                            )}
                        </div>
                        <div style="margin-top: 5px; font-size: 12px; color: #999;">
                            ※ 画像が登録されていません
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # 選択解除ボタン
            st.markdown("")
            if st.button("選択を解除", width="stretch"):
                st.session_state.selected_part = None
                st.rerun()
else:
    st.info("👆 上の一覧から部品を選択すると、詳細情報が表示されます。")

# フッター
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 12px;">
        部品検査箇所表示システム v1.0
    </div>
    """,
    unsafe_allow_html=True
)
