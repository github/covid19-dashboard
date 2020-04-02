import pandas as pd


base_url = 'https://raw.githubusercontent.com/pratapvardhan/notebooks/master/covid19/'
paths = {
    'mapping': base_url + 'mapping_countries.csv',
    'overview': base_url + 'overview.tpl'
}


def get_mappings(url):
    df = pd.read_csv(url, encoding='utf-8')
    return {
        'df': df,
        'replace.country': dict(df.dropna(subset=['Name']).set_index('Country')['Name']),
        'map.continent': dict(df.set_index('Name')['Continent'])
    }


mapping = get_mappings(paths['mapping'])


def get_template(path):
    from urllib.parse import urlparse
    if bool(urlparse(path).netloc):
        from urllib.request import urlopen
        return urlopen(path).read().decode('utf8')
    return open(path, encoding='utf8').read()


def get_frame(name):
    url = (
        'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/'
        f'csse_covid_19_time_series/time_series_covid19_{name}_global.csv')
    df = pd.read_csv(url, encoding='utf-8')
    # rename countries
    df['Country/Region'] = df['Country/Region'].replace(mapping['replace.country'])
    return df


def get_dates(df):
    dt_cols = df.columns[~df.columns.isin(['Province/State', 'Country/Region', 'Lat', 'Long'])]
    latest_date_idx = -1
    # sometimes last column may be empty, then go backwards
    for i in range(-1, -len(dt_cols), -1):
        if not df[dt_cols[i]].fillna(0).eq(0).all():
            latest_date_idx = i
            break
    return latest_date_idx, dt_cols


def gen_data(region='Country/Region', filter_frame=lambda x: x, add_table=[], kpis_info=[]):
    col_region = region
    df = get_frame('confirmed')
    dft_cases = df.pipe(filter_frame)
    dft_deaths = get_frame('deaths').pipe(filter_frame)
    latest_date_idx, dt_cols = get_dates(df)
    dt_today = dt_cols[latest_date_idx]
    dt_5ago = dt_cols[latest_date_idx - 5]

    dfc_cases = dft_cases.groupby(col_region)[dt_today].sum()
    dfc_deaths = dft_deaths.groupby(col_region)[dt_today].sum()
    dfp_cases = dft_cases.groupby(col_region)[dt_5ago].sum()
    dfp_deaths = dft_deaths.groupby(col_region)[dt_5ago].sum()

    df_table = (pd.DataFrame(dict(
        Cases=dfc_cases, Deaths=dfc_deaths,
        PCases=dfp_cases, PDeaths=dfp_deaths))
        .sort_values(by=['Cases', 'Deaths'], ascending=[False, False])
        .reset_index())
    for c in 'Cases, Deaths'.split(', '):
        df_table[f'{c} (+)'] = (df_table[c] - df_table[f'P{c}']).clip(0)  # DATABUG
    df_table['Fatality Rate'] = (100 * df_table['Deaths'] / df_table['Cases']).round(1)

    for rule in add_table:
        df_table[rule['name']] = df_table.pipe(rule['apply'])

    def kpi_of(name, prefix, pipe):
        df_f = df_table.pipe(pipe or (lambda x: x[x[col_region].eq(name)]))
        return df_f[metrics].sum().add_prefix(prefix)

    metrics = ['Cases', 'Deaths', 'Cases (+)', 'Deaths (+)']
    s_kpis = pd.concat([
        kpi_of(x['title'], f'{x["prefix"]} ', x.get('pipe'))
        for x in kpis_info])
    summary = {'updated': pd.to_datetime(dt_today), 'since': pd.to_datetime(dt_5ago)}
    summary = {**summary, **df_table[metrics].sum(), **s_kpis}
    dft_ct_cases = dft_cases.groupby(col_region)[dt_cols].sum()
    dft_ct_new_cases = dft_ct_cases.diff(axis=1).fillna(0).astype(int)
    return {
        'summary': summary, 'table': df_table, 'newcases': dft_ct_new_cases,
        'dt_last': latest_date_idx, 'dt_cols': dt_cols}


def gen_data_us(region='Province/State', kpis_info=[]):
    col_region = region
    df = pd.read_csv(
        'https://raw.githubusercontent.com/nytimes/covid-19-data'
        '/master/us-states.csv')
    dt_today = df['date'].max()
    dt_5ago = (pd.to_datetime(dt_today) - pd.Timedelta(days=5)).strftime('%Y-%m-%d')
    cols = ['cases', 'deaths']
    df_table = df[df['date'].eq(dt_today)].set_index('state')[cols].join(
        df[df['date'].eq(dt_5ago)].set_index('state')[cols], rsuffix='Ago'
    ).reset_index().fillna(0)
    for col in cols:
        df_table[f'{col.title()} (+)'] = df_table[col] - df_table[f'{col}Ago']
    df_table = df_table.rename(
        columns={'state': col_region, 'cases': 'Cases', 'deaths': 'Deaths'})
    df_table['Fatality Rate'] = (100 * df_table['Deaths'] / df_table['Cases']).round(1)
    df_table = df_table.sort_values(by='Cases', ascending=False)
    dft_ct_cases = df.set_index(['state', 'date'])['cases'].unstack(1, fill_value=0)
    
    metrics = ['Cases', 'Deaths', 'Cases (+)', 'Deaths (+)']

    def kpi_of(name, prefix, pipe):
        df_f = df_table.pipe(pipe or (lambda x: x[x[col_region].eq(name)]))
        return df_f[metrics].sum().add_prefix(prefix)

    s_kpis = pd.concat([
        kpi_of(x['title'], f'{x["prefix"]} ', x.get('pipe'))
        for x in kpis_info])
    summary = {'updated': pd.to_datetime(dt_today), 'since': pd.to_datetime(dt_5ago)}
    summary = {**summary, **df_table[metrics].sum(), **s_kpis}
    dft_ct_new_cases = dft_ct_cases.diff(axis=1).fillna(0).astype(int)
    data = {'summary': summary, 'table': df_table, 'newcases': dft_ct_new_cases}
    return data