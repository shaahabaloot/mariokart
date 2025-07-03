# top.py (プリセットボタン追加版)

import streamlit as st
import pandas as pd
import config 
# --- データ準備 ---
# ファイルが存在しない場合のエラーハンドリング
try:
    df_char_raw = pd.read_csv('characters_jp_0703.csv')
    df_machine = pd.read_csv('machines_jp_0703.csv')
except FileNotFoundError as e:
    st.error(f"エラー: ファイルが見つかりません。'{e.filename}' をこのアプリと同じフォルダに配置してください。")
    st.stop()


# 同じ性能のキャラは最初の1人のみ取得する
stat_columns = ['Road', 'Terrain', 'Water', 'Unknown', 'Accel/MT', 'Weight', 'Handling']
df_char = df_char_raw.groupby(stat_columns, as_index=False).agg(
    Character=('Character', 'first')
)

# --- WebアプリケーションのUI設定 ---
st.set_page_config(layout="wide",
                    page_title=config.PAGE_TITLE,
                    page_icon=config.PAGE_ICON
                    )
st.title('🏎️ マリオカートワールド カスタム検索')
with st.sidebar:
    st.header("アプリ情報")

    # 情報元
    st.markdown("""
    **【情報元】**
    
    [こちらのスプレッドシート](https://docs.google.com/spreadsheets/d/1t3BeXH3shj6Rh7x0ROFD81ZBxyumQFs9pebbnYcfWi4/edit?pli=1&gid=735843013#gid=735843013)の
    2025年7月3日時点での情報を元にしています。
    """)

    # 作成者
    st.markdown("""
    **【作成者】**
    
    [カスタニエ](https://x.com/kc1game)
    """)
    st.markdown("""
    **【連絡先】**
    
    [こちらから](https://forms.gle/KxHfwzQqhgBFFWvn6)
    """)
# st.expanderを使って、開閉可能なUIを作成
with st.expander("⚙️ 検索条件を設定する", expanded=True):

    # ▼▼▼ 変更点: プリセットボタンを追加 ▼▼▼

    # session_stateを初期化（アプリの初回実行時のみ）
    if 'target_accel' not in st.session_state:
        st.session_state.target_accel = 15 # デフォルト値

    st.write("**目標とする加速の値**")
    # st.columnsでボタンを横に並べる
    b_col1, b_col2, b_col3 = st.columns(3)

    with b_col1:
        # ボタンが押されたら、session_stateの値を更新
        if st.button("中量級 (11)", use_container_width=True):
            st.session_state.target_accel = 11
    with b_col2:
        if st.button("軽量級 (14)", use_container_width=True):
            st.session_state.target_accel = 14
    with b_col3:
        if st.button("タイムアタック (0)", use_container_width=True):
            st.session_state.target_accel = 0

    # 目標とする加速(Accel)の値
    # keyを指定して、session_stateとnumber_inputを連携させる
    target_accel = st.number_input(
        '数値入力',
        min_value=0,
        max_value=30,
        key='target_accel' # session_stateのキーと一致させる
    )

    st.write('---') # 区切り線
    st.write('**速度の重視比率**')
    # st.columnsを使ってスライダーを横に3つ並べる
    col1, col2, col3 = st.columns(3)
    with col1:
        w_road = st.slider('舗装道路[%]', 0, 100, 50, key='w_road')
    with col2:
        w_terrain = st.slider('オフロード[%]', 0, 100, 25, key='w_terrain')
    with col3:
        w_water = st.slider('水上[%]', 0, 100, 25, key='w_water')


# --- 計算処理 ---
combinations = df_char.merge(df_machine, how='cross', suffixes=('_char', '_machine'))
base_bonus = 3
stats_to_calc = ['Road', 'Terrain', 'Water', 'Accel/MT', 'Weight', 'Handling']
for stat in stats_to_calc:
    combinations[f'Total_{stat}'] = combinations[f'{stat}_char'] + combinations[f'{stat}_machine'] + base_bonus
filtered_combinations = combinations[combinations['Total_Accel/MT'] >= target_accel].copy()
total_weight = w_road + w_terrain + w_water
if total_weight > 0:
    w_road_norm = w_road / total_weight
    w_terrain_norm = w_terrain / total_weight
    w_water_norm = w_water / total_weight
else:
    w_road_norm, w_terrain_norm, w_water_norm = 0, 0, 0
filtered_combinations['Weighted_Speed'] = (
    filtered_combinations['Total_Road'] * w_road_norm +
    filtered_combinations['Total_Terrain'] * w_terrain_norm +
    filtered_combinations['Total_Water'] * w_water_norm
)
sorted_results = filtered_combinations.sort_values(by='Weighted_Speed', ascending=False)


# --- 結果表示 ---
st.header('🔍 検索結果')
st.write(f"**目標加速: `{target_accel}` 以上** の組み合わせを、**重み付け速度**が高い順に表示します。")
st.write(f"速度の重視比率: **舗装道路 `{w_road}`%**, **オフロード `{w_terrain}`%**, **水上 `{w_water}`%**")

if sorted_results.empty:
    st.warning('条件に一致する組み合わせが見つかりませんでした。')
else:
    display_columns = {
        'Character': 'キャラクター',
        'Vehicle': 'マシン',
        'Weighted_Speed': '速度スコア',
        'Total_Road': '速度(舗装)',
        'Total_Terrain': '速度(オフ)',
        'Total_Water': '速度(水上)',
        'Total_Accel/MT': '加速',
        'Total_Handling': '曲がり',
        'Total_Weight': '重さ'
    }
    display_df = sorted_results[display_columns.keys()].rename(columns=display_columns)

    st.dataframe(
        display_df,
        column_config={
            "速度スコア": st.column_config.NumberColumn(format="%.2f"),
        },
        hide_index=True,
        height=600
    )