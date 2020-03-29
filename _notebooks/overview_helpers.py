import os
from urllib import request

import pandas as pd

data_folder = os.path.join(os.path.dirname(__file__), '../_data')


class SourceData:
    df_mappings = pd.read_csv(os.path.join(data_folder, 'mapping_countries.csv'))

    mappings = {'replace.country': dict(df_mappings.dropna(subset=['Name'])
                                        .set_index('Country')['Name']),
                'map.continent': dict(df_mappings.set_index('Name')['Continent'])
                }

    @classmethod
    def get_overview_template(cls):
        with open(os.path.join(data_folder, 'overview.tpl')) as f:
            return f.read()

    @classmethod
    def get_covid_dataframe(cls, name):
        url = (
            'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/'
            f'csse_covid_19_time_series/time_series_covid19_{name}_global.csv')
        df = pd.read_csv(url)
        # rename countries
        df['Country/Region'] = df['Country/Region'].replace(cls.mappings['replace.country'])
        return df

    @staticmethod
    def get_dates(df):
        dt_cols = df.columns[~df.columns.isin(['Province/State', 'Country/Region', 'Lat', 'Long'])]
        LAST_DATE_I = -1
        # sometimes last column may be empty, then go backwards
        for i in range(-1, -len(dt_cols), -1):
            if not df[dt_cols[i]].fillna(0).eq(0).all():
                LAST_DATE_I = i
                break
        return LAST_DATE_I, dt_cols


class OverviewData:
    COL_REGION = 'Country/Region'
    ABS_COLS = ['Cases', 'Deaths', 'Cases (+)', 'Deaths (+)']

    dft_cases = SourceData.get_covid_dataframe('confirmed')
    dft_deaths = SourceData.get_covid_dataframe('deaths')
    dft_recovered = SourceData.get_covid_dataframe('recovered')
    LAST_DATE_I, dt_cols = SourceData.get_dates(dft_cases)

    dt_today = dt_cols[LAST_DATE_I]
    dfc_cases = dft_cases.groupby(COL_REGION)[dt_today].sum()
    dfc_deaths = dft_deaths.groupby(COL_REGION)[dt_today].sum()

    PREV_LAG = 5
    dt_lag = dt_cols[LAST_DATE_I - PREV_LAG]

    @classmethod
    def lagged_cases(cls, lag=PREV_LAG):
        return cls.dft_cases.groupby(cls.COL_REGION)[cls.dt_cols[cls.LAST_DATE_I - lag]].sum()

    @classmethod
    def lagged_deaths(cls, lag=PREV_LAG):
        return cls.dft_deaths.groupby(cls.COL_REGION)[cls.dt_cols[cls.LAST_DATE_I - lag]].sum()

    @classmethod
    def overview_table(cls):
        df_table = (pd.DataFrame(dict(Cases=cls.dfc_cases,
                                      Deaths=cls.dfc_deaths,
                                      PCases=cls.lagged_cases(),
                                      PDeaths=cls.lagged_deaths()))
                    .sort_values(by=['Cases', 'Deaths'], ascending=[False, False])
                    .reset_index())
        df_table.rename(columns={'index': 'Country/Region'}, inplace=True)
        for c in 'Cases, Deaths'.split(', '):
            df_table[f'{c} (+)'] = (df_table[c] - df_table[f'P{c}']).clip(0)  # DATA BUG
        df_table['Fatality Rate'] = (100 * df_table['Deaths'] / df_table['Cases']).round(1)
        df_table['Continent'] = df_table['Country/Region'].map(SourceData.mappings['map.continent'])

        # remove problematic
        df_table = df_table[~df_table['Country/Region'].isin(['Cape Verde', 'Cruise Ship', 'Kosovo'])]
        return df_table

    @classmethod
    def make_summary_dict(cls):
        df_table = cls.overview_table()

        metrics = cls.ABS_COLS
        s_china = df_table[df_table['Country/Region'].eq('China')][metrics].sum().add_prefix('China ')
        s_us = df_table[df_table['Country/Region'].eq('US')][metrics].sum().add_prefix('US ')
        s_eu = df_table[df_table['Continent'].eq('Europe')][metrics].sum().add_prefix('EU ')
        summary = {'updated': pd.to_datetime(cls.dt_today), 'since': pd.to_datetime(cls.dt_lag)}
        summary = {**summary, **df_table[metrics].sum(), **s_china, **s_us, **s_eu}
        return summary

    @classmethod
    def make_new_cases_arrays(cls, n_days=50):
        dft_ct_cases = cls.dft_cases.groupby(cls.COL_REGION)[cls.dt_cols].sum()
        dft_ct_new_cases = dft_ct_cases.diff(axis=1).fillna(0).astype(int)
        return dft_ct_new_cases.loc[:, cls.dt_cols[cls.LAST_DATE_I - n_days]:cls.dt_cols[cls.LAST_DATE_I]]


class WordPopulation:
    csv_path = os.path.join(data_folder, 'world_population.csv')

    @classmethod
    def download(cls):
        # !pip install beautifulsoup4
        import bs4 as bs

        # read html
        world_population_page = 'https://www.worldometers.info/world-population/population-by-country/'
        source = request.urlopen(world_population_page).read()
        soup = bs.BeautifulSoup(source, 'lxml')

        # get pandas df
        table = soup.find_all('table')
        df = pd.read_html(str(table))[0]

        # clean up df
        rename_map = {'Country (or dependency)': 'country',
                      'Population (2020)': 'population',
                      'Land Area (Km²)': 'area',
                      'Urban Pop %': 'urban_ratio',
                      }
        df_clean = df.rename(rename_map, axis=1)[rename_map.values()]
        df_clean['urban_ratio'] = pd.to_numeric(df_clean['urban_ratio'].str.extract(r'(\d*)')[0]) / 100
        df.to_csv(cls.csv_path, index=None)

    @classmethod
    def load(cls):
        if not os.path.exists(cls.csv_path):
            cls.download()
        return pd.read_csv(cls.csv_path)


class OverviewDataExtras(OverviewData):
    ABS_COLS_MAP = {'Cases': 'Cases.total',
                    'Deaths': 'Deaths.total',
                    'Cases (+)': 'Cases.new',
                    'Deaths (+)': 'Deaths.new'}
    ABS_COLS_RENAMED = list(ABS_COLS_MAP.values())
    PER_100K_COLS = [f'{c}.per100k' for c in ABS_COLS_RENAMED]
    CASES_COLS = ABS_COLS_RENAMED[::2] + PER_100K_COLS[::2]
    EST_COLS = [f'{c}.est' for c in CASES_COLS]

    @classmethod
    def populations_df(cls):
        df_pop = WordPopulation.load().rename(columns={'country': cls.COL_REGION})
        df_pop[cls.COL_REGION] = df_pop[cls.COL_REGION].map({
            'United States': 'US',
            'Czech Republic (Czechia)': 'Czechia',
            'Taiwan': 'Taiwan*',
            'State of Palestine': 'West Bank and Gaza',
            'Côte d\'Ivoire': 'Cote d\'Ivoire',
        }).fillna(df_pop[cls.COL_REGION])
        return df_pop

    @classmethod
    def overview_table_with_per_100k(cls):
        df = (cls.overview_table()
              .rename(columns=cls.ABS_COLS_MAP)
              .drop(['PCases', 'PDeaths'], axis=1))

        df_pop = cls.populations_df()

        df = df[df[cls.COL_REGION].isin(df_pop[cls.COL_REGION])].copy()

        # align populations
        df = pd.merge(df, df_pop[[cls.COL_REGION, 'population']],
                      on=cls.COL_REGION, how='left')

        for col, per_100k_col in zip(cls.ABS_COLS_RENAMED, cls.PER_100K_COLS):
            df[per_100k_col] = df[col] * 1e5 / df['population']

        return df.set_index(cls.COL_REGION, drop=True).sort_values('Cases.new', ascending=False)

    @classmethod
    def table_with_estimated_cases(cls, death_lag=8):
        """
        Assumptions:
            - unbiased (if everyone is tested) mortality rate is
                around 1.5% (from what was found in heavily tested countries)
            - it takes on average 8 days after being reported case (tested positive)
                to die and become reported death.
            - testing ratio / bias (how many are suspected tested) of countries
                didn't change significantly during the last 8 days.
            - Recent new cases can be adjusted using the same testing_ratio bias.
        """
        probable_unbiased_mortality_rate = 0.015  # Diamond Princess / Kuwait / South Korea
        lagged_mortality_rate = (cls.dfc_deaths + 1) / (cls.lagged_cases(death_lag) + 1)
        testing_bias = lagged_mortality_rate / probable_unbiased_mortality_rate

        df = cls.overview_table_with_per_100k()
        df = df.join(testing_bias.to_frame('testing_bias'), how='left')

        for col, est_col in zip(cls.CASES_COLS, cls.EST_COLS):
            df[est_col] = df['testing_bias'] * df[col]

        return df.sort_values('Cases.new.est', ascending=False)

    @classmethod
    def table_with_projections(cls):
        df = cls.table_with_estimated_cases()

        df['immune_ratio'] = df['Cases.total.est'] / df['population']

        cur_growth_rate = (cls.lagged_cases(cls.PREV_LAG) / cls.lagged_cases(cls.PREV_LAG * 2)
                           ).pow(1 / cls.PREV_LAG)

        t_bias = df['testing_bias']
        pop = df['population']

        # initialise
        rec_time = 20
        rec = cls.lagged_cases(rec_time) * t_bias / pop
        active = (cls.dfc_cases * t_bias - rec) / pop
        sus = 1 - rec - active

        ICU_ratio = 0.06

        df = df.join(cur_growth_rate.to_frame('growth_rate'), how='left')
        df = df.join((active * pop * ICU_ratio / 1e5).to_frame('needICU.per100k'), how='left')

        # simulate
        col_days = [14, 30, 60]
        for i in range(1, col_days[-1] + 1):
            active, rec = active * sus * cur_growth_rate, rec + active / rec_time
            sus = 1 - rec - active

            if i in col_days:
                df = df.join((active * pop * ICU_ratio / 1e5)
                             .to_frame(f'needICU.per100k.+{i}d'), how='left')
                df = df.join((1 - sus)
                             .to_frame(f'immune_ratio.+{i}d'), how='left')

        return df

    @classmethod
    def filter_df(cls, df):
        df = df.drop(['Continent', 'population', 'testing_bias'], axis=1)
        return df[df['Deaths.total'] > 10][df.columns.sort_values()]


def pandas_console_options():
    pd.set_option('display.max_colwidth', 300)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)


def overview_html():
    template_text = SourceData.get_overview_template()

    import numpy as np
    import pandas as pd
    from jinja2 import Template
    from IPython.display import HTML

    helper = OverviewData
    template = Template(template_text)
    html = template.render(
        D=helper.make_summary_dict(),
        table=helper.overview_table(),
        newcases=helper.make_new_cases_arrays(),
        np=np, pd=pd, enumerate=enumerate)
    return HTML(f'<div>{html}</div>')
