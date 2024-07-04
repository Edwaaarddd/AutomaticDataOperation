import streamlit as st
import pandas as pd

def convert_revenue_to_float(revenue_str):
    return float(revenue_str.replace('USD ', '').replace(',', ''))

def extract_country_name(column_name):
    return column_name.split(':')[-1].strip()

def process_revenue_data(hok_df, country_region):
    hok_revenue_columns = [col for col in hok_df.columns if col not in ['Date', 'Notes']]
    for column in hok_revenue_columns:
        hok_df[column] = hok_df[column].astype(str).apply(convert_revenue_to_float)
    hok_long = hok_df.melt(id_vars=['Date'], value_vars=hok_revenue_columns,
                           var_name='Country', value_name='Revenue')
    hok_long['Country'] = hok_long['Country'].apply(extract_country_name)
    hok_long = hok_long.merge(country_region, left_on='Country', right_on='国家名称', how='left')
    not_found = hok_long[hok_long['所属区域'].isna()]['Country'].unique()
    if len(not_found) > 0:
        st.warning(f"未找到对应区域的国家: {', '.join(not_found)}")
    hok_grouped = hok_long.groupby(['Date', '所属区域']).agg({'Revenue': 'sum'}).reset_index()
    hok_grouped.columns = ['Date', 'Region', 'Gross daily revenue']
    return hok_grouped

def process_units_data(hok_units_df, country_region):
    hok_units_columns = [col for col in hok_units_df.columns if col not in ['Date', 'Notes']]
    for column in hok_units_columns:
        hok_units_df[column] = pd.to_numeric(hok_units_df[column].astype(str).str.replace(',', ''), errors='coerce').fillna(0).astype(int)
    hok_units_long = hok_units_df.melt(id_vars=['Date'], value_vars=hok_units_columns,
                                       var_name='Country', value_name='Units')
    hok_units_long['Country'] = hok_units_long['Country'].apply(extract_country_name)
    hok_units_long = hok_units_long.merge(country_region, left_on='Country', right_on='国家名称', how='left')
    not_found = hok_units_long[hok_units_long['所属区域'].isna()]['Country'].unique()
    if len(not_found) > 0:
        st.warning(f"未找到对应区域的国家: {', '.join(not_found)}")
    hok_units_grouped = hok_units_long.groupby(['Date', '所属区域']).agg({'Units': 'sum'}).reset_index()
    hok_units_grouped.columns = ['Date', 'Region', 'Units']
    return hok_units_grouped

def main():
    st.title('GP游戏数据处理程序')
    
    # 文件上传
    hok_users_top10_file = st.file_uploader('上传 Users Top10 文件', type='csv')
    hok_users_top20_file = st.file_uploader('上传 Users Top20 文件', type='csv')
    hok_users_top30_file = st.file_uploader('上传 Users Top30 文件', type='csv')
    hok_revenue_top10_file = st.file_uploader('上传 Revenue Top10 文件', type='csv')
    hok_revenue_top20_file = st.file_uploader('上传 Revenue Top20 文件', type='csv')
    hok_revenue_top30_file = st.file_uploader('上传 Revenue Top30 文件', type='csv')
    country_region_file = st.file_uploader('上传 国家地区对照表 文件', type='xlsx')
    
    final_output_path = st.text_input('请输入最终汇总表的保存路径', '/Users/fan/Desktop/HOK/HOK_最终汇总表.xlsx')

    # 用户输入游戏名称和日期格式
    game_name = st.text_input('请输入游戏名称', 'HOK')
    date_format = st.text_input('请输入日期格式（如 %b %d, %Y 或 %b %Y 等）', '%b %d, %Y')
    
    if st.button('处理数据'):
        try:
            if hok_users_top10_file is not None:
                hok_users_top10 = pd.read_csv(hok_users_top10_file)
            if hok_users_top20_file is not None:
                hok_users_top20 = pd.read_csv(hok_users_top20_file)
            if hok_users_top30_file is not None:
                hok_users_top30 = pd.read_csv(hok_users_top30_file)
            if hok_revenue_top10_file is not None:
                hok_revenue_top10 = pd.read_csv(hok_revenue_top10_file)
            if hok_revenue_top20_file is not None:
                hok_revenue_top20 = pd.read_csv(hok_revenue_top20_file)
            if hok_revenue_top30_file is not None:
                hok_revenue_top30 = pd.read_csv(hok_revenue_top30_file)
            if country_region_file is not None:
                country_region = pd.read_excel(country_region_file)

            # 处理收入和用户数据
            hok_revenue_top10_grouped = process_revenue_data(hok_revenue_top10, country_region)
            hok_revenue_top20_grouped = process_revenue_data(hok_revenue_top20, country_region)
            hok_revenue_top30_grouped = process_revenue_data(hok_revenue_top30, country_region)
            hok_units_top10_grouped = process_units_data(hok_users_top10, country_region)
            hok_units_top20_grouped = process_units_data(hok_users_top20, country_region)
            hok_units_top30_grouped = process_units_data(hok_users_top30, country_region)

            # 合并收入数据
            all_revenue_data = pd.concat([hok_revenue_top10_grouped,
                                          hok_revenue_top20_grouped, hok_revenue_top30_grouped])

            # 合并用户数据
            all_units_data = pd.concat([hok_units_top10_grouped,
                                        hok_units_top20_grouped, hok_units_top30_grouped])

            # 按日期和区域再次分组汇总，确保没有重复数据
            consolidated_revenue_df = all_revenue_data.groupby(['Date', 'Region']).agg({'Gross daily revenue': 'sum'}).reset_index()
            consolidated_units_df = all_units_data.groupby(['Date', 'Region']).agg({'Units': 'sum'}).reset_index()

            # 合并收入和用户获取数据
            final_grouped_df = pd.merge(consolidated_units_df, consolidated_revenue_df, on=['Date', 'Region'], how='outer').fillna(0)

            # 添加固定的 Title 和 Platform 列
            final_grouped_df['Title'] = game_name
            final_grouped_df['Platform'] = 'GP'

            # 将列重新排列为所需的顺序
            final_grouped_df = final_grouped_df[['Date', 'Title', 'Platform', 'Region', 'Units', 'Gross daily revenue']]

            # 将日期转换为 datetime 格式进行排序，然后再转换回用户指定的格式
            final_grouped_df['Date'] = pd.to_datetime(final_grouped_df['Date'], format=date_format, errors='coerce')
            final_grouped_df = final_grouped_df.sort_values(by='Date')
            final_grouped_df['Date'] = final_grouped_df['Date'].dt.strftime(date_format)

            # 显示最终数据框
            st.dataframe(final_grouped_df)

            # 保存最终数据框到 Excel 文件
            final_grouped_df.to_excel(final_output_path, index=False)
            st.success(f"文件已保存到 {final_output_path}")
        except Exception as e:
            st.error(f"处理数据时发生错误: {e}")

if __name__ == '__main__':
    main()