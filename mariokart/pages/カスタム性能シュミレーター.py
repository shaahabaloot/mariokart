# pages/2_カスタム性能シュミレーター.py

import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("🔧 カスタム性能シュミレーター")

# --- データ準備 ---
# ファイルが存在しない場合のエラーハンドリング
try:
    # 今回はキャラクターをグループ化しない
    df_char = pd.read_csv('characters_jp_0703.csv')
    df_machine = pd.read_csv('machines_jp_0703.csv')
except FileNotFoundError as e:
    st.error(f"エラー: ファイルが見つかりません。'{e.filename}' をメインアプリと同じフォルダに配置してください。")
    st.stop()

# 計算対象のステータス列を定義
stat_columns = ['Road', 'Terrain', 'Water', 'Accel/MT', 'Weight', 'Handling']

# --- UI: キャラクターとマシンの選択 ---
st.header("① キャラクターとマシンを選択")
col1, col2 = st.columns(2)
with col1:
    # キャラクターを選択 (CSVの順番)
    selected_char_name = st.selectbox(
    "キャラクターを選択",
    df_char['Character']  # sorted()を削除し、DataFrameの列を直接渡す
)
with col2:
    # マシンを選択 (CSVの順番)
    selected_machine_name = st.selectbox(
        "マシンを選択",
        df_machine['Vehicle']  # sorted()を削除し、DataFrameの列を直接渡す
    )

# --- 選択された組み合わせの総合性能を計算・表示 ---
st.header("② 選択したカスタムの総合性能")

# 選択されたキャラとマシンのステータスを取得
char_stats = df_char[df_char['Character'] == selected_char_name].iloc[0]
machine_stats = df_machine[df_machine['Vehicle'] == selected_machine_name].iloc[0]

# 総合性能を計算
total_stats = {}
base_bonus = 3
for stat in stat_columns:
    total_stats[stat] = char_stats[stat] + machine_stats[stat] + base_bonus

# 計算結果をデータフレームに変換して表示
total_stats_df = pd.DataFrame([total_stats])
# 列の表示名を日本語にマッピング
column_mapping = {
    'Road': '速度(舗装)', 'Terrain': '速度(オフ)', 'Water': '速度(水上)',
    'Unknown': '不明', 'Accel/MT': '加速', 'Weight': '重さ', 'Handling': '曲がりやすさ'
}
total_stats_df = total_stats_df.rename(columns=column_mapping)
st.dataframe(total_stats_df, hide_index=True)


# --- 同じ性能になる組み合わせを検索・表示 ---
st.header("③ 同じ総合性能になる組み合わせ一覧")

# 1. 全ての組み合わせを作成
all_combos = df_char.merge(df_machine, how='cross', suffixes=('_char', '_machine'))

# 2. 全ての組み合わせの総合性能を計算
for stat in stat_columns:
    all_combos[f'Total_{stat}'] = all_combos[f'{stat}_char'] + all_combos[f'{stat}_machine'] + base_bonus

# 3. 選択したカスタムと同じ総合性能を持つ組み合わせをフィルタリング
query_parts = []
for stat in stat_columns:
    # 計算済みの総合性能（total_stats）と比較
    query_parts.append(f"`Total_{stat}` == {total_stats[stat]}")

query = " & ".join(query_parts)
equivalent_combos_df = all_combos.query(query)

# 表示する列を絞り、名前を変更
display_df = equivalent_combos_df[['Character', 'Vehicle']].rename(
    columns={'Character': 'キャラクター', 'Vehicle': 'マシン'}
)

if display_df.empty:
    st.info("同じ性能になる他の組み合わせは見つかりませんでした。")
else:
    st.dataframe(display_df, hide_index=True, use_container_width=True)