import os
from urllib import request

import pandas as pd

data_folder = (os.path.join(os.path.dirname(__file__), 'data_files')
               if '__file__' in locals() else 'data_files')


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
    page = 'https://www.worldometers.info/world-population/population-by-country/'

    @classmethod
    def scrape(cls):
        # !pip install beautifulsoup4
        # !pip install lxml
        import bs4

        # read html
        source = request.urlopen(cls.page).read()
        soup = bs4.BeautifulSoup(source, 'lxml')

        # get pandas df
        table = soup.find_all('table')
        return pd.read_html(str(table))[0]

    @classmethod
    def download(cls):
        df = cls.scrape()

        # clean up df
        rename_map = {'Country (or dependency)': 'country',
                      'Population (2020)': 'population',
                      'Land Area (Km²)': 'area',
                      'Urban Pop %': 'urban_ratio',
                      }
        df_clean = df.rename(rename_map, axis=1)[rename_map.values()]
        df_clean['urban_ratio'] = pd.to_numeric(df_clean['urban_ratio'].str.extract(r'(\d*)')[0]) / 100
        df_clean.to_csv(cls.csv_path, index=None)

    @classmethod
    def load(cls):
        if not os.path.exists(cls.csv_path):
            cls.download()
        return pd.read_csv(cls.csv_path)


class HostpitalBeds(WordPopulation):
    csv_path = os.path.join(data_folder, 'hospital_beds.csv')
    page = 'https://en.wikipedia.org/wiki/List_of_countries_by_hospital_beds'

    @classmethod
    def download(cls):
        df_wiki = cls.scrape()

        # clean up df wikie
        df_wiki = df_wiki.droplevel([0, 1], axis=1)

        rename_map = {'Country/territory': 'country',
                      'ICU-CCB beds/100,000 inhabitants': 'icu_per_100k',
                      df_wiki.columns[df_wiki.columns.str.startswith('Occupancy')][0]: 'occupancy',
                      '2017': 'beds_per_1000_2017',
                      }
        df_clean = df_wiki.rename(rename_map, axis=1)[rename_map.values()]
        df_clean['icu_per_100k'] = pd.to_numeric(df_clean['icu_per_100k'].str
                                                 .replace(r'\[\d*\]', ''))

        # load df for asian countries
        # file manually created from
        # https://www.researchgate.net/publication/338520008_Critical_Care_Bed_Capacity_in_Asian_Countries_and_Regions
        df_asia = pd.read_csv(os.path.join(data_folder, 'ccb_asian_countries.csv'))
        df_clean = pd.concat([df_clean,
                              df_asia[~df_asia['country'].isin(df_clean['country'])]])

        df_clean.to_csv(cls.csv_path, index=None)


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
        return df_pop.set_index(cls.COL_REGION)

    @classmethod
    def beds_df(cls):
        df_beds = HostpitalBeds.load().rename(columns={'country': cls.COL_REGION})
        df_beds[cls.COL_REGION] = df_beds[cls.COL_REGION].map({
            'United States': 'US',
            'United Kingdom (more)': 'United Kingdom',
            'Czech Republic': 'Czechia',
        }).fillna(df_beds[cls.COL_REGION])
        return df_beds.set_index(cls.COL_REGION)

    @classmethod
    def overview_table_with_per_100k(cls):
        df = (cls.overview_table()
              .rename(columns=cls.ABS_COLS_MAP)
              .drop(['PCases', 'PDeaths'], axis=1)
              .set_index(cls.COL_REGION, drop=True)
              .sort_values('Cases.new', ascending=False))
        df['Fatality Rate'] /= 100

        df_pop = cls.populations_df()

        df['population'] = df_pop['population']
        df.dropna(subset=['population'], inplace=True)

        for col, per_100k_col in zip(cls.ABS_COLS_RENAMED, cls.PER_100K_COLS):
            df[per_100k_col] = df[col] * 1e5 / df['population']

        return df

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
        testing_bias[testing_bias < 1] = 1

        df = cls.overview_table_with_per_100k()
        df['testing_bias'] = testing_bias

        for col, est_col in zip(cls.CASES_COLS, cls.EST_COLS):
            df[est_col] = df['testing_bias'] * df[col]

        return df.sort_values('Cases.new.est', ascending=False)

    @classmethod
    def smoothed_growth_rates(cls, n_days):
        recent_dates = cls.dt_cols[-n_days:]

        cases = (cls.dft_cases.groupby(cls.COL_REGION).sum()[recent_dates] + 1)  # with pseudo counts

        diffs = cls.dft_cases.groupby(cls.COL_REGION).sum().diff(axis=1)[recent_dates]

        # dates with larger number of cases have higher sampling accuracy
        # so their measurement deserve more confidence
        sampling_weights = (cases.T / cases.sum(axis=1).T).T

        # daily rate is new / (total - new)
        daily_growth_rates = cases / (cases - diffs)

        weighted_growth_rate = (daily_growth_rates * sampling_weights).sum(axis=1)

        return weighted_growth_rate

    @classmethod
    def table_with_icu_capacities(cls):
        df = cls.table_with_estimated_cases()

        df_beds = cls.beds_df()

        df['icu_capacity_per100k'] = df_beds['icu_per_100k']

        # occupancy 66% for us:
        #   https://www.sccm.org/Blog/March-2020/United-States-Resource-Availability-for-COVID-19
        # occupancy average 75% for OECD:
        #   https://www.oecd-ilibrary.org/social-issues-migration-health/health-at-a-glance-2019_4dd50c09-en
        df['icu_spare_capacity_per100k'] = df['icu_capacity_per100k'] * 0.3
        return df

    @classmethod
    def table_with_projections(cls, projection_days=(7, 14, 30, 60, 90), plot_countries=()):
        df = cls.table_with_icu_capacities()

        df['affected_ratio'] = df['Cases.total'] / df['population']

        past_recovered, past_active, simulation_start_day = (
            cls._calculate_recovered_and_active_until_now(df))

        df, past_recovered, past_active = cls._run_SIR_model_forward(
            df,
            past_recovered=past_recovered,
            past_active=past_active,
            projection_days=projection_days)

        if len(plot_countries):
            cls._plot_SIR_for_countries(plot_countries=plot_countries,
                                        past_recovered=past_recovered,
                                        past_active=past_active,
                                        simulation_start_day=simulation_start_day,
                                        growth_rate=df['growth_rate'])
        return df


    @classmethod
    def _calculate_recovered_and_active_until_now(cls, df, recovery_lagged9_rate=0.07):
        # estimated daily cases ratio of population
        lagged_cases_ratios = (cls.dft_cases.groupby(cls.COL_REGION).sum()[cls.dt_cols].T *
                               df['testing_bias'].T / df['population'].T).T
        # protect from testing bias over-inflation
        lagged_cases_ratios[lagged_cases_ratios > 1] = 1

        # run through history and estimate recovered and active using:
        # https://covid19dashboards.com/outstanding_cases/#Appendix:-Methodology-of-Predicting-Recovered-Cases
        recs, actives = [], []
        zeros_series = lagged_cases_ratios[cls.dt_cols[0]] * 0  # this is to have consistent types
        day = 0
        for day in range(len(cls.dt_cols)):
            prev_rec = recs[day - 1] if day > 0 else zeros_series
            tot_lagged_9 = lagged_cases_ratios[cls.dt_cols[day - 9]] if day >= 8 else zeros_series
            recs.append(prev_rec + (tot_lagged_9 - prev_rec) * recovery_lagged9_rate)
            actives.append(lagged_cases_ratios[cls.dt_cols[day]] - recs[day])

        return recs, actives, day

    @classmethod
    def _run_SIR_model_forward(cls,
                               df,
                               past_recovered,
                               past_active,
                               projection_days,
                               recovery_lagged9_rate=0.07):

        cur_growth_rate = cls.smoothed_growth_rates(n_days=cls.PREV_LAG)
        df['growth_rate'] = (cur_growth_rate - 1)

        cur_recovery_rate = (past_recovered[-1] - past_recovered[-2]) / past_active[-1]
        infect_rate = cur_growth_rate - 1 + cur_recovery_rate

        ICU_ratio = 0.06
        rec_rate_simple = 0.05

        # simulate
        df['peak_icu_neek_per100k'] = 0
        for day in range(1, projection_days[-1] + 1):
            # calculate susceptible
            sus = 1 - past_recovered[-1] - past_active[-1]

            # calculate new recovered
            actives_lagged_9 = past_active[-9]
            delta_rec = actives_lagged_9 * recovery_lagged9_rate
            delta_rec_simple = past_active[-1] * rec_rate_simple
            # limit recovery rate to simple SIR model where
            # lagged rate estimation becomes too high (on the downward slopes)
            delta_rec[delta_rec > delta_rec_simple] = delta_rec_simple[delta_rec > delta_rec_simple]
            new_recovered = past_recovered[-1] + delta_rec

            # calculate new active
            delta_infect = past_active[-1] * sus * infect_rate
            new_active = past_active[-1] + delta_infect - delta_rec
            new_active[new_active < 0] = 0

            # update
            past_recovered.append(new_recovered)
            past_active.append(new_active)

            icu_need = past_active[-1] * df['population'] * ICU_ratio / 1e5

            df['peak_icu_neek_per100k'] = pd.concat([df['peak_icu_neek_per100k'],
                                                     icu_need], axis=1).max(axis=1)
            if day == 1 or day in projection_days:
                suffix = f'.+{day}d' if day > 1 else ''
                df[f'needICU.per100k{suffix}'] = icu_need
                df[f'affected_ratio.est{suffix}'] = 1 - sus

        return df, past_recovered, past_active

    @classmethod
    def _plot_SIR_for_countries(cls, plot_countries, past_recovered,
                                past_active, simulation_start_day, growth_rate):
        for debug_country in plot_countries:
            debug = [{'day': day - simulation_start_day,
                      'Susceptible': (1 - a - r)[debug_country],
                      'Infected': a[debug_country],
                      'Removed': r[debug_country]}
                     for day, (r, a) in enumerate(zip(past_recovered, past_active))
                     if day > simulation_start_day]

            title = (f"{debug_country}: "
                     f"Growth Rate: {growth_rate[debug_country]:.0%}. "
                     f"S/I/R init: {debug[0]['Susceptible']:.1%},"
                     f"{debug[0]['Infected']:.1%},{debug[0]['Removed']:.1%}")
            pd.DataFrame(debug).set_index('day').plot(title=title)

    @classmethod
    def filter_df(cls, df):
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
