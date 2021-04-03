import functools
import os
import re
from typing import Tuple, List
from urllib import request

import numpy as np
import pandas as pd
import altair as alt

data_folder = (os.path.join(os.path.dirname(__file__), 'data_files')
               if '__file__' in locals() else 'data_files')

COL_REGION = 'Country/Region'

pd.set_option('display.max_colwidth', 300)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 10000)

SAVE_JHU_DATA = False

func_cache = functools.lru_cache(maxsize=None)  # simple memory caching


class SourceData:
    df_mappings = pd.read_csv(os.path.join(data_folder, 'mapping_countries.csv'))

    mappings = {'replace.country': dict(df_mappings.dropna(subset=['Name'])
                                        .set_index('Country')['Name']),
                'map.continent': dict(df_mappings.set_index('Name')['Continent'])
                }

    @classmethod
    def _cache_csv_path(cls, name):
        return os.path.join(data_folder, f'covid_jhu/{name}_transposed.csv')

    @classmethod
    def _save_covid_df(cls, df, name):
        df.T.to_csv(cls._cache_csv_path(name))

    @classmethod
    def _load_covid_df(cls, name):
        df = pd.read_csv(cls._cache_csv_path(name), index_col=0).T
        df[df.columns[2:]] = df[df.columns[2:]].apply(pd.to_numeric, errors='coerce')
        return df

    @classmethod
    def _download_covid_df(cls, name):
        url = ('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/'
               f'csse_covid_19_time_series/time_series_covid19_{name}_global.csv')
        df = pd.read_csv(url)
        return df

    @classmethod
    def get_covid_dataframe(cls, name):
        df = cls._download_covid_df(name)
        if SAVE_JHU_DATA:
            cls._save_covid_df(df, name)

        # rename countries
        df[COL_REGION] = df[COL_REGION].replace(cls.mappings['replace.country'])
        return df

    @staticmethod
    def get_dates(df):
        return df.columns[~df.columns.isin(['Province/State', COL_REGION, 'Lat', 'Long'])]


class OWID:
    # data docs: https://github.com/owid/covid-19-data/tree/master/public/data

    # large file
    url_full = 'https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv'
    # only the latest slice
    url_latest = 'https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/latest/owid-covid-latest.csv'

    icu_per_mil_col = 'icu_patients_per_million'
    vaccination_percent_col = 'total_vaccinations_per_hundred'

    @classmethod
    @func_cache
    def latest_snapshot(cls):
        df_raw = pd.read_csv(cls.url_latest)
        df = (df_raw
              .rename(columns={'location': COL_REGION})
              .dropna(subset=[COL_REGION]))
        df[COL_REGION] = df[COL_REGION].replace({
            'United States': 'US',
            'Taiwan': 'Taiwan*',
            'Democratic Republic of Congo': 'Congo (Kinshasa)',
            'Congo': 'Congo (Brazzaville)',
            'Myanmar': 'Burma',
            'Palestine': 'West Bank and Gaza',
            'Timor': 'Timor-Leste',
        })
        return df.set_index(COL_REGION)

    @classmethod
    def latest_icu_per_mil(cls):
        return cls.latest_snapshot()[cls.icu_per_mil_col].dropna()

    @classmethod
    def latest_vaccination_percent(cls):
        return cls.latest_snapshot()[cls.vaccination_percent_col].dropna()


class AgeAdjustedData:
    # https://population.un.org/wpp/Download/Standard/Population/
    # https://population.un.org/wpp/Download/Files/1_Indicators%20(Standard)/EXCEL_FILES/1_Population/WPP2019_POP_F07_1_POPULATION_BY_AGE_BOTH_SEXES.xlsx
    csv_path = os.path.join(data_folder, 'world_pop_age_2020.csv')

    class Cols:
        # o = original
        o4 = '0-4'
        o9 = '5-9'
        o14 = '10-14'
        o19 = '15-19'
        o24 = '20-24'
        o29 = '25-29'
        o34 = '30-34'
        o39 = '35-39'
        o44 = '40-44'
        o49 = '45-49'
        o54 = '50-54'
        o59 = '55-59'
        o64 = '60-64'
        o69 = '65-69'
        o74 = '70-74'
        o79 = '75-79'
        o84 = '80-84'
        o89 = '85-89'
        o94 = '90-94'
        o99 = '95-99'
        o100p = '100+'

    # paper: https://www.nature.com/articles/s41586-020-2918-0#MOESM1
    # table S3 from supplementary material:
    #   https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-020-2918-0/MediaObjects/41586_2020_2918_MOESM1_ESM.pdf
    intl_ifrs = pd.Series({
        Cols.o4: 0.003,
        Cols.o9: 0.001,
        Cols.o14: 0.001,
        Cols.o19: 0.003,
        Cols.o24: 0.006,
        Cols.o29: 0.013,
        Cols.o34: 0.024,
        Cols.o39: 0.040,
        Cols.o44: 0.075,
        Cols.o49: 0.121,
        Cols.o54: 0.207,
        Cols.o59: 0.323,
        Cols.o64: 0.456,
        Cols.o69: 1.075,
        Cols.o74: 1.674,
        Cols.o79: 3.203,
        Cols.o84: 8.292,  # 80+ is a single bucket in that paper
        Cols.o89: 8.292,
        Cols.o94: 8.292,
        Cols.o99: 8.292,
        Cols.o100p: 8.292,
    })
    intl_ifrs *= 0.01  # convert from percent to ratio

    @classmethod
    def load(cls):
        df_raw = pd.read_csv(cls.csv_path)

        df_filt = df_raw[df_raw['Type'].isin(['Subregion', 'Country/Area'])]

        df_filt = (df_filt
                   .drop(columns=['Index', 'Variant', 'Notes', 'Country code', 'Parent code',
                                  'Reference date (as of 1 July)', 'Type'])
                   .rename(columns={'Region, subregion, country or area *': COL_REGION}))

        # adjust country names
        df_filt[COL_REGION] = df_filt[COL_REGION].map({
            'United States of America': 'US',
            'China, Taiwan Province of China': 'Taiwan*',
            'United Republic of Tanzania': 'Tanzania',
            'Iran (Islamic Republic of)': 'Iran',
            'Republic of Korea': 'South Korea',
            'Bolivia (Plurinational State of)': 'Bolivia',
            'Venezuela (Bolivarian Republic of)': 'Venezuela',
            'Republic of Moldova': 'Moldova',
            'Russian Federation': 'Russia',
            'State of Palestine': 'West Bank and Gaza',
            'Côte d\'Ivoire': 'Cote d\'Ivoire',
            'Democratic Republic of the Congo': 'Congo (Kinshasa)',
            'Congo': 'Congo (Brazzaville)',
            'Syrian Arab Republic': 'Syria',
            'Myanmar': 'Burma',
            'Viet Nam': 'Vietnam',
            'Brunei Darussalam': 'Brunei',
            'Lao People\'s Democratic Republic': 'Laos'
        }).fillna(df_filt[COL_REGION])

        df_num = df_filt.set_index(COL_REGION)

        # convert to numbers
        df_num = df_num.apply(lambda s:
                              pd.Series(s)
                              .str.replace(' ', '')
                              .apply(pd.to_numeric, errors='coerce'))

        population_s = df_num.sum(1) * 1000

        # convert to ratios
        df_pct = (df_num.T / df_num.sum(1)).T

        # calculate IFR
        ifr_s = pd.Series(np.dot(df_pct, cls.intl_ifrs), index=df_pct.index)

        ## icu need estimation
        ## https://www.imperial.ac.uk/media/imperial-college/medicine/sph/ide/gida-fellowships/Imperial-College-COVID19-NPI-modelling-16-03-2020.pdf
        ## 4.4% serious symptomatic cases for UK
        ## adjusting here by age by using IFRs ratios
        ## adjusting by UK's past testing bias (14) since the 4.4% figure is for reported cases
        icu_percent_s = 0.044 * (ifr_s / ifr_s['United Kingdom']) / 14

        return ifr_s, population_s, icu_percent_s


class ScrapedTableBase:
    page = 'https://page.com/table'
    file_name = 'file.csv'

    @classmethod
    def csv_path(cls):
        return os.path.join(data_folder, cls.file_name)

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
    def load(cls):
        if not os.path.exists(cls.csv_path()):
            cls.download()
        return pd.read_csv(cls.csv_path())

    @classmethod
    def download(cls):
        df = cls.scrape()
        df.to_csv(cls.csv_path(), index=False)


class HostpitalBeds(ScrapedTableBase):
    file_name = 'hospital_beds.csv'
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

        df_clean.to_csv(cls.csv_path(), index=False)


class EmojiFlags(ScrapedTableBase):
    file_name = 'emoji_flags.csv'
    page = 'https://apps.timwhitlock.info/emoji/tables/iso3166'

    emoji_col = 'emoji_code'

    @classmethod
    def download(cls):
        df = cls.scrape()
        df_filt = df.rename(columns={'Name': COL_REGION,
                                     'Unicode': cls.emoji_col}
                            ).drop(columns=['Emoji'])

        # rename countries
        df_filt[COL_REGION] = df_filt[COL_REGION].map({
            'United States': 'US',
            'Taiwan': 'Taiwan*',
            'Macedonia': 'North Macedonia',
            'Cape Verde': 'Cabo Verde',
            'Saint Vincent and The Grenadines': 'Saint Vincent and the Grenadines',
            'Palestinian Territory': 'West Bank and Gaza',
            'Côte D\'Ivoire': 'Cote d\'Ivoire',
            'Syrian Arab Republic': 'Syria',
            'Myanmar': 'Burma',
            'Viet Nam': 'Vietnam',
            'Brunei Darussalam': 'Brunei',
            'Lao People\'s Democratic Republic': 'Laos',
             'Czech Republic': 'Czechia',
        }).fillna(df_filt[COL_REGION])

        # congo
        df_filt.loc[df_filt['ISO'] == 'CD', COL_REGION] = 'Congo (Kinshasa)'
        df_filt.loc[df_filt['ISO'] == 'CG', COL_REGION] = 'Congo (Brazzaville)'

        # convert emoji hex codes to decimal
        df_filt[cls.emoji_col] = df_filt[cls.emoji_col].apply(
            lambda s: ''.join(f'&#{int(hex, 16)};'
                              for hex in re.findall(r'U\+(\S+)', s)))

        df_filt.to_csv(cls.csv_path(), index=False)


class CovidData:
    COL_REGION = COL_REGION
    CASES_TOT = 'Cases.total'
    CASES_NEW = 'Cases.new'
    DEATHS_TOT = 'Deaths.total'
    DEATHS_NEW = 'Deaths.new'

    PER_100K_SUFFIX = '.per100k'

    dft_cases_raw = SourceData.get_covid_dataframe('confirmed')
    dft_deaths_raw = SourceData.get_covid_dataframe('deaths')
    # dft_recovered = SourceData.get_covid_dataframe('recovered')
    dt_cols_all = SourceData.get_dates(dft_cases_raw)

    cur_date = pd.to_datetime(dt_cols_all[-1]).date().isoformat()

    PREV_LAG = 5

    # modeling constants
    ## testing bias
    death_lag = 8

    def __init__(self, days_offset=0):
        assert days_offset <= 0, 'day_offest can only be 0 or negative (in the past)'
        self.dt_cols = self.dt_cols_all[:(len(self.dt_cols_all) + days_offset)]
        self.dft_cases_backfilled = self._cases_with_backfilled_unreported_days()[self.dt_cols]
        self.dft_deaths = self.dft_deaths_raw.groupby(COL_REGION).sum()[self.dt_cols]
        self.dfc_cases = self.dft_cases_backfilled[self.dt_cols[-1]]
        self.dfc_deaths = self.dft_deaths[self.dt_cols[-1]]

        # to be calculated later
        self.testing_biases_dft: pd.DataFrame = None
        self.cases_est_dft: pd.DataFrame = None

    def _cases_with_backfilled_unreported_days(self):

        def backfill_missing(series, backfill_prev_threshold=50):
            """
            Fills 0 diff days between days with large measurements by spreading the
            future's "catch up" day's cases on the zero days.

            :param series: pandas series of daily cases
            :param backfill_prev_threshold: number of cases per day after which a 0 day
                is considered a missing measurement rather than a true zero
            :return: backfilled series of daily cases
            """
            out = [series[0]]
            missing = 0
            for cur in series[1:]:
                if cur == 0:
                    if out[-1] >= backfill_prev_threshold:
                        # a lot of cases on previous appended day
                        missing += 1  # increase missing days
                    else:
                        # normal: too few cases previously, a zero is plausible
                        out.append(cur)
                elif cur > 0:
                    if missing:
                        # catching up by backfilling from current value
                        out.extend([cur / (missing + 1)] * (missing + 1))
                        missing = 0  # reset missing condition
                    else:
                        # normal: cases accumulating
                        out.append(cur)
                else:  # cur < 0
                    # some kind of data adjustment (e.g. France)
                    if missing:  # reset missing
                        out.extend([0] * missing)
                        missing = 0
                    out.append(cur)

            if missing:  # finished on missing (no "catch up" day until now)
                out.extend([0] * missing)

            return pd.Series(out, index=series.index)

        cases = self.dft_cases_raw.groupby(self.COL_REGION).sum()[self.dt_cols_all]
        diffs = cases.diff(axis=1)
        diffs.iloc[:, 0] = cases.iloc[:, 0]  # replace resulting nans in first date's data

        fixed = diffs.apply(backfill_missing, axis=1)
        imputed_cases = fixed.cumsum(axis=1)
        return imputed_cases

    def lagged_cases(self, lag=PREV_LAG):
        return self.dft_cases_backfilled[self.dt_cols[-lag]]

    def lagged_deaths(self, lag=PREV_LAG):
        return self.dft_deaths[self.dt_cols[-lag]]

    def add_last_dates(self, df):

        def last_date(s):
            non_zero_s = s[4:][s[4:] > 0]
            if len(non_zero_s):
                return pd.to_datetime(non_zero_s.index[-1]).date().isoformat()
            else:
                return float('nan')

        df['last_case_date'] = (self.dft_cases_raw.groupby(COL_REGION).sum().diff(axis=1)
                                .apply(last_date, axis=1))
        df['last_death_date'] = (self.dft_deaths_raw.groupby(COL_REGION).sum().diff(axis=1)
                                 .apply(last_date, axis=1))
        return df

    def overview_table(self):
        df_table = (pd.DataFrame({'Cases.total': self.dfc_cases,
                                  'Deaths.total': self.dfc_deaths,
                                  'Cases.total.prev': self.lagged_cases(),
                                  'Deaths.total.prev': self.lagged_deaths()})
                    .sort_values(by=['Cases.total', 'Deaths.total'], ascending=[False, False])
                    .reset_index())
        df_table.rename(columns={'index': COL_REGION}, inplace=True)
        for c in [self.CASES_TOT, self.DEATHS_TOT]:
            df_table[c.replace('total', 'new')] = (
                    df_table[c] - df_table[f'{c}.prev']).clip(0)  # DATA BUG
        df_table['Fatality Rate'] = (100 * df_table['Deaths.total'] /
                                     df_table['Cases.total']).round(1)
        df_table['Continent'] = df_table[COL_REGION].map(SourceData.mappings['map.continent'])

        # remove problematic
        df_table = df_table[~df_table[COL_REGION].isin(['Cape Verde', 'Cruise Ship', 'Kosovo'])]
        return df_table

    @classmethod
    def beds_df(cls):
        df_beds = HostpitalBeds.load().rename(columns={'country': COL_REGION})
        df_beds[COL_REGION] = df_beds[COL_REGION].map({
            'United States': 'US',
            'United Kingdom (more)': 'United Kingdom',
            'Czech Republic': 'Czechia',
        }).fillna(df_beds[COL_REGION])
        return df_beds.set_index(COL_REGION)

    def overview_table_with_extra_data(self):
        df = (self.overview_table()
              .drop(['Cases.total.prev', 'Deaths.total.prev'], axis=1)
              .set_index(COL_REGION, drop=True)
              .sort_values('Cases.new', ascending=False))
        df['Fatality Rate'] /= 100

        # add emoji flags
        df['emoji_flag'] = EmojiFlags.load().set_index(COL_REGION)[EmojiFlags.emoji_col]
        df['emoji_flag'] = df['emoji_flag'].fillna('')

        # last dates
        df = self.add_last_dates(df)

        # age adjusted data
        (df['age_adjusted_ifr'],
         df['population'],
         df['age_adjusted_icu_percentage']) = AgeAdjustedData.load()

        # add per population columns
        df.dropna(subset=['population'], inplace=True)
        for col in [self.CASES_TOT, self.DEATHS_TOT, self.CASES_NEW, self.DEATHS_NEW]:
            df[f'{col}{self.PER_100K_SUFFIX}'] = df[col] * 1e5 / df['population']

        # add ICU capacity data
        df_beds = self.beds_df()
        df['icu_capacity_per100k'] = df_beds['icu_per_100k']

        # add OWID data
        df['owid_icu_per_100k'] = OWID.latest_icu_per_mil() / 10
        df['owid_vaccination_ratio'] = OWID.latest_vaccination_percent() / 100

        return df

    def calculate_testing_biases_dft(
            self, ifrs: pd.Series, min_window_lag = 60, min_window_deaths = 300
    ) -> pd.DataFrame:
        deaths_dft = self.dft_deaths
        cases_dft = self.dft_cases_backfilled

        def biases_vec(country: str) -> pd.Series:
            d_vec = deaths_dft.loc[country].values
            c_vec = cases_dft.loc[country].values
            ifr = ifrs.loc[country]
            left, right = self.death_lag, self.death_lag + min_window_lag
            biases = np.ones_like(c_vec)

            # short circuit and fallback if not enough data for windowed calculations
            if d_vec[-1] < min_window_deaths:
                if d_vec[-1] > 0:
                    biases[:] = (d_vec[-1] / c_vec[-1]) / ifr
                else:
                    pass  # just return ones

            else:
                def diff_deaths(right, left):
                    return d_vec[right] - d_vec[left]

                def diff_cases(right, left):
                    return c_vec[right - self.death_lag] - c_vec[left - self.death_lag]

                while right <= (len(c_vec) - 1):
                    if ((right - left) < min_window_lag or
                            diff_deaths(right, left) < min_window_deaths):
                        # grow window to the right if needed
                        right += 1
                        continue

                    while ((right - left) > min_window_lag and
                           diff_deaths(right, left) > min_window_deaths):
                        # shrink window from the left if possible
                        left += 1

                    biases[right] = ((diff_deaths(right, left) / diff_cases(right, left))
                                     / ifr)
                    # advance left every time to prevent infinite loop
                    left += 1

                # use first non 1 (initialised) value to fill the initial values
                fill_ind = np.where(biases != 1)[0][0]
                biases[:fill_ind] = biases[fill_ind]

            return pd.Series(biases, index=self.dt_cols)

        testing_biases_dft = ifrs.index.to_series().apply(biases_vec)
        testing_biases_dft[testing_biases_dft < 1] = 1
        return testing_biases_dft

    def table_with_estimated_cases(self):
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
        df = self.overview_table_with_extra_data()

        self.testing_biases_dft = self.calculate_testing_biases_dft(
            df['age_adjusted_ifr'])

        # adjust daily cases by closest approximation of testing bias at that point
        cases_dft = self.dft_cases_backfilled
        self.cases_est_dft = (cases_dft.diff(axis=1) * self.testing_biases_dft
                              ).cumsum(axis=1).fillna(0).astype(int)

        df['current_testing_bias'] = self.testing_biases_dft.iloc[:, -1]

        # total cases
        df[f'{self.CASES_TOT}.est'] = self.cases_est_dft[self.dt_cols[-1]]
        df[f'{self.CASES_TOT}{self.PER_100K_SUFFIX}.est'] = (
                df[f'{self.CASES_TOT}.est'] * 1e5 / df['population'])

        # new cases just need adjustments with current bias
        for col in [self.CASES_NEW, f'{self.CASES_NEW}{self.PER_100K_SUFFIX}']:
            df[f'{col}.est'] = df['current_testing_bias'] * df[col]

        return df

    @classmethod
    def filter_df(cls, df, cases_filter=1000, deaths_filter=20, population_filter=3e5):
        return df[((df['Cases.total'] > cases_filter) |
                   (df['Deaths.total'] > deaths_filter)) &
                  (df['population'] > population_filter)][df.columns.sort_values()]

    @classmethod
    def rename_long_names(cls, df):
        return df.rename(index={'Bosnia and Herzegovina': 'Bosnia',
                                'United Arab Emirates': 'UAE',
                                'Central African Republic': 'CAR (Africa)',
                                })

    def smoothed_growth_rates(self, n_days):
        recent_dates = self.dt_cols[-n_days:]

        cases = self.cases_est_dft[recent_dates] + 1  # with pseudo counts

        diffs = self.cases_est_dft.diff(axis=1)[recent_dates]
        diffs[diffs < 0] = 0  # total cases cannot go down

        cases, diffs = cases.T, diffs.T  # broadcasting works correctly this way

        # daily rate is new / (total - new)
        daily_growth_rates = cases / (cases - diffs)

        # dates with larger number of cases have higher sampling accuracy
        # so their measurement deserve more confidence
        sampling_weights = (cases / cases.sum(0))

        weighted_mean = (daily_growth_rates * sampling_weights).sum(0)

        weighted_std = ((daily_growth_rates - weighted_mean).pow(2) *
                        sampling_weights).sum(0).pow(0.5)

        return weighted_mean - 1, weighted_std

    def table_with_current_rates_and_ratios(
            self) -> Tuple[pd.DataFrame, List[pd.Series], List[pd.Series]]:
        df = self.table_with_estimated_cases()

        df['affected_ratio'] = df['Cases.total'] / df['population']

        df['growth_rate'], df['growth_rate_std'] = self.smoothed_growth_rates(n_days=self.PREV_LAG)

        past_active, past_recovered = self._calculate_recovered_and_active_until_now(df)

        df['current_active_ratio'] = past_active[-1].fillna(0)
        df['current_recovered_ratio'] = past_recovered[-1].fillna(0)

        df['transmission_rate'], df['transmission_rate_std'] = Model.growth_to_transmission_rate(
            growth=df['growth_rate'],
            rec=df['current_recovered_ratio'],
            act=df['current_active_ratio'],
            growth_std=df['growth_rate_std'])

        return df, past_active, past_recovered

    def table_with_projections(self, projection_days=(7, 14, 30), debug_dfs=False):

        df, past_active, past_recovered = self.table_with_current_rates_and_ratios()

        df, traces = Model.run_model_forward(
            df,
            past_active=past_active.copy(),
            past_recovered=past_recovered.copy(),
            projection_days=projection_days)

        if debug_dfs:
            debug_dfs = Model.timeseries_for_countries(
                debug_countries=df.index,
                traces=traces,
                simulation_start_day=len(past_recovered) - 1,
                infection_rate=df['transmission_rate'])
            return df, debug_dfs
        return df

    def _calculate_recovered_and_active_until_now(self, df):
        # estimated daily cases ratios of population
        lagged_cases_ratios = (self.cases_est_dft[self.dt_cols].T / df['population'].T).T
        # protect from testing bias over-inflation
        lagged_cases_ratios[lagged_cases_ratios > 1] = 1

        # run through history and estimate recovered and active using:
        # https://covid19dashboards.com/outstanding_cases/#Appendix:-Methodology-of-Predicting-Recovered-Cases
        actives, recs = [], []
        zeros_series = lagged_cases_ratios[self.dt_cols[0]] * 0  # this is to have consistent types
        for day in range(len(self.dt_cols)):
            # previous day
            prev_rec = recs[day - 1] if day > 0 else zeros_series
            # lagged recoveries
            tot_lagged_9 = lagged_cases_ratios[self.dt_cols[day - 9]] if day >= 9 else zeros_series
            new_recs = prev_rec + (tot_lagged_9 - prev_rec) * Model.recovery_lagged9_rate
            # clip recoveries by current cases
            cur_cases = lagged_cases_ratios[self.dt_cols[day]]
            new_recs[new_recs > cur_cases] = cur_cases[new_recs > cur_cases]
            new_actives = cur_cases - new_recs
            # assign
            recs.append(new_recs)
            actives.append(new_actives)

        return actives, recs


class Model:
    ## recovery estimation
    recovery_lagged9_rate = 0.07
    ## sir model
    rec_rate_simple = 0.05

    @classmethod
    def run_model_forward(cls,
                          df,
                          past_active,
                          past_recovered,
                          projection_days,
                          ):

        sus, act, rec = cls._run_sir_model(
            past_recovered, past_active, df['growth_rate'], n_days=projection_days[-1])

        # sample more growth rates
        sus_lists = [[s] for s in sus]
        act_lists = [[a] for a in act]
        rec_lists = [[r] for r in rec]

        for ratio in np.linspace(-1, 1, 10):
            pert_growth = df['growth_rate'] + ratio * df['growth_rate_std']
            pert_growth[pert_growth < 0] = 0
            sus_other, act_other, rec_other = cls._run_sir_model(
                past_recovered, past_active, pert_growth, n_days=projection_days[-1])
            for s_list, s in zip(sus_lists, sus_other):
                s_list.append(s)
            for a_list, a in zip(act_lists, act_other):
                a_list.append(a)
            for r_list, r in zip(rec_lists, rec_other):
                r_list.append(r)

        def list_to_max_min(l):
            concated = [pd.concat(sub_l, axis=1) for sub_l in l]
            max_list, min_list = zip(*[(d.max(1), d.min(1)) for d in concated])
            return max_list, min_list

        sus_max, sus_min = list_to_max_min(sus_lists)
        act_max, act_min = list_to_max_min(act_lists)
        rec_max, rec_min = list_to_max_min(rec_lists)

        day_one = len(past_recovered)
        for day in [1] + list(projection_days):
            ind = day_one + day - 1
            suffix = f'.+{day}d' if day > 1 else ''

            icu_max = df['age_adjusted_icu_percentage'] * 1e5

            df[f'needICU.per100k{suffix}'] = act[ind] * icu_max
            df[f'needICU.per100k{suffix}.max'] = act_max[ind] * icu_max
            df[f'needICU.per100k{suffix}.min'] = act_min[ind] * icu_max
            df[f'needICU.per100k{suffix}.err'] = (act_max[ind] - act_min[ind]) * icu_max / 2

            df[f'affected_ratio.est{suffix}'] = 1 - sus[ind]
            df[f'affected_ratio.est{suffix}.max'] = 1 - sus_min[ind]
            df[f'affected_ratio.est{suffix}.min'] = 1 - sus_max[ind]
            df[f'affected_ratio.est{suffix}.err'] = (sus_max[ind] - sus_min[ind]) / 2

        traces = {
            'sus_center': sus, 'sus_max': sus_max, 'sus_min': sus_min,
            'act_center': act, 'act_max': act_max, 'act_min': act_min,
            'rec_center': rec, 'rec_max': rec_max, 'rec_min': rec_min,
        }

        return df, traces

    @classmethod
    def growth_to_transmission_rate(cls, growth, rec, act, growth_std=None):
        daily_delta = growth
        tot = rec + act
        active = act
        # Explanation of the formula below:
        #   daily delta = delta total / total
        #   daily delta = new-infected / total
        #   daily_delta = infect_rate * active * (1 - tot) / tot, so solving for infect_rate:
        infect_rate = (daily_delta * tot) / ((1 - tot) * active)

        # standard deviation
        infect_std = 0
        if growth_std is not None:
            # higher bound
            infect_higher = ((daily_delta + growth_std) * tot) / ((1 - tot) * active)

            # lower bound
            growth_lower = daily_delta - growth_std
            growth_lower[growth_lower < 0] = 0
            infect_lower = (growth_lower * tot) / ((1 - tot) * active)

            infect_std = (infect_higher - infect_lower) / 2

        return infect_rate, infect_std

    @classmethod
    def _run_sir_model(cls, past_rec, past_act, growth, n_days):
        rec, act = past_rec.copy(), past_act.copy()

        infect_rate, _ = cls.growth_to_transmission_rate(growth, rec[-1], act[-1])

        # simulate
        for i in range(n_days):
            # calculate susceptible
            sus = 1 - rec[-1] - act[-1]

            # calculate new recovered
            actives_lagged_9 = act[-9]
            delta_rec = actives_lagged_9 * cls.recovery_lagged9_rate
            delta_rec_simple = act[-1] * cls.rec_rate_simple
            # limit recovery rate to simple SIR model where
            # lagged rate estimation becomes too high (on the downward slopes)
            delta_rec[delta_rec > delta_rec_simple] = delta_rec_simple[delta_rec > delta_rec_simple]
            new_recovered = rec[-1] + delta_rec

            # calculate new active
            delta_infect = act[-1] * sus * infect_rate
            new_active = act[-1] + delta_infect - delta_rec
            new_active[new_active < 0] = 0

            # update
            rec.append(new_recovered)
            act.append(new_active)

        sus = [1 - r - a for r, a in zip(rec, act)]

        return sus, act, rec

    @staticmethod
    def timeseries_for_countries(debug_countries, traces,
                                 simulation_start_day, infection_rate):
        dfs = []
        for debug_country in debug_countries:
            debug = [{'day': day - simulation_start_day,
                      'Susceptible': traces['sus_center'][day][debug_country],
                      'Susceptible.max': traces['sus_max'][day][debug_country],
                      'Susceptible.min': traces['sus_min'][day][debug_country],
                      'Infected': traces['act_center'][day][debug_country],
                      'Infected.max': traces['act_max'][day][debug_country],
                      'Infected.min': traces['act_min'][day][debug_country],
                      'Removed': traces['rec_center'][day][debug_country],
                      'Removed.max': traces['rec_max'][day][debug_country],
                      'Removed.min': traces['rec_min'][day][debug_country],
                      }
                     for day in range(len(traces['rec_center']))]

            title = (f"{debug_country}: "
                     f"Transmission Rate: {infection_rate[debug_country]:.1%}. "
                     f"S/I/R init: {debug[0]['Susceptible']:.1%},"
                     f"{debug[0]['Infected']:.1%},{debug[0]['Removed']:.1%}")
            df = pd.DataFrame(debug).set_index('day')
            df['title'] = title
            df['country'] = debug_country
            dfs.append(df)
        return dfs


def altair_sir_plot(df_alt, default_country):
    alt.data_transformers.disable_max_rows()

    select_country = alt.selection_single(
        name='Select',
        fields=['country'],
        init={'country': default_country},
        bind=alt.binding_select(options=sorted(df_alt['country'].unique()))
    )

    title = (alt.Chart(df_alt[['country', 'title']].drop_duplicates())
             .mark_text(dy=-180, dx=0, size=16)
             .encode(text='title:N')
             .transform_filter(select_country))

    base = alt.Chart(df_alt).encode(x='day:Q')

    line_cols = ['Infected', 'Removed']  # 'Susceptible'
    colors = ['red', 'green']
    lines = (base.mark_line()
             .transform_fold(line_cols)
             .encode(x=alt.X('day:Q', title=f'days relative to today ({CovidData.cur_date})'),
                     y=alt.Y('value:Q',
                             axis=alt.Axis(format='%', title='Percentage of Population')),
                     color=alt.Color('key:N',
                                     scale=alt.Scale(domain=line_cols, range=colors))))

    import functools
    bands = functools.reduce(alt.Chart.__add__,
                             [base.mark_area(opacity=0.1, color=color)
                             .encode(y=f'{col}\.max:Q', y2=f'{col}\.min:Q')
                              for col, color in zip(line_cols, colors)])

    today_line = (alt.Chart(pd.DataFrame({'x': [0]}))
                  .mark_rule(color='orange')
                  .encode(x='x', size=alt.value(1)))

    return ((lines + bands + title + today_line)
            .add_selection(select_country)
            .transform_filter(select_country)
            .configure_title(fontSize=20)
            .configure_axis(labelFontSize=15, titleFontSize=18, grid=True)
            .properties(width=550, height=340))


def altair_multiple_countries_infected(df_alt_all,
                                       countries,
                                       title,
                                       days_back=120,
                                       marker_day=10):
    if not len(countries):
        return

    alt.data_transformers.disable_max_rows()

    df_alt = df_alt_all[df_alt_all['day'].between(-days_back, 0) &
                        (df_alt_all['country'].isin(countries)) &
                        (df_alt_all['Infected'] > 0)]

    select_country = alt.selection_single(
        name='Select',
        fields=['country'],
        bind='legend',
        empty='all',
        init={'country': countries[0]}
    )

    today_line = (alt.Chart(pd.DataFrame({'x': [-marker_day]}))
                  .mark_rule(color='#c8d1ce')
                  .encode(x='x', strokeWidth=alt.value(6), opacity=alt.value(0.5)))

    lines = (alt.Chart(df_alt).mark_line().encode(
        x=alt.X('day:Q',
                scale=alt.Scale(type='symlog'),
                axis=alt.Axis(labelOverlap='greedy', values=list(range(-days_back, 0, 5)),
                              title=f'days relative to today ({CovidData.cur_date})')),
        y=alt.Y('Infected:Q',
                scale=alt.Scale(type='log'),
                axis=alt.Axis(format='%', title='Infected percentage'),
                ),
        color=alt.Color('country:N',
                        legend=alt.Legend(title='Country',
                                          labelFontSize=14,
                                          values=countries.to_list())),
        opacity=alt.condition(select_country, alt.value(1), alt.value(0.4)),
        strokeWidth=alt.condition(select_country, alt.value(4), alt.value(2)))
    )

    return ((lines + today_line)
            .add_selection(select_country)
            .configure_title(fontSize=20)
            .configure_axis(labelFontSize=15, titleFontSize=18, grid=True)
            .properties(title=title, width=550, height=340).interactive(bind_x=False))


class PandasStyling:

    @staticmethod
    def country_index_emoji_link(df, font_size=3):
        """Assumes index is country names and "emoji_flag" field exists
        and adds a news link and the country's emoji"""
        df = CovidData.rename_long_names(df)
        df.index = df.apply(
            lambda s: f"""
            <font size={font_size}>{s['emoji_flag']} <a href=
            "https://duckduckgo.com/?q=covid19 pandemic in {s.name} country" 
            target="_blank">{s.name}</a></font>""", axis=1)
        return df

    @staticmethod
    def add_bar(s_t, s_v, color):
        s_v = s_v.copy()
        s_v[s_v > 1] = 1
        s_v[s_v < 0] = 0
        return [f'background: linear-gradient(90deg, {color} {v:.0%}, transparent {v:.0%})'
                for t, v in zip(s_t, s_v)]

    @staticmethod
    def with_errs_float(df, val_col, err_col):
        s = df.apply(lambda r: f"<b>{r[val_col]:.1f}</b>  \
            ± <font size=1><i>{r[err_col]:.1f}</i></font>", axis=1)
        s[2 * df[err_col] > df[val_col]] = '<font size=1><i>noisy data</i></font>'
        return s

    @staticmethod
    def with_errs_ratio(df, val_col, err_col):
        s = df.apply(lambda r: f"<b>{r[val_col]:.1%}</b>  \
            ± <font size=1><i>{r[err_col]:.1%}</i></font>", axis=1)
        s[2 * df[err_col] > df[val_col]] = '<font size=1><i>noisy data</i></font>'
        return s


class GeoMap:

    @classmethod
    def get_world_geo_df(cls):
        import geopandas

        shapefile = 'data_files/50m_countries/ne_50m_admin_0_countries.shp'

        world = geopandas.read_file(shapefile)[['ADMIN', 'ADM0_A3', 'geometry']]
        world.columns = ['country', 'iso_code', 'geometry']
        world = world[world['country'] != "Antarctica"].copy()
        world['country'] = world['country'].map({
            'United States of America': 'US',
            'Taiwan': 'Taiwan*',
            'Palestine': 'West Bank and Gaza',
            'Côte d\'Ivoire': 'Cote d\'Ivoire',
            'Bosnia and Herz.': 'Bosnia and Herzegovina',
        }).fillna(world['country'])
        return world

    @classmethod
    def make_geo_df(cls, df_all, cases_filter=1000, deaths_filter=20):
        world = cls.get_world_geo_df()

        df_plot = (df_all.reset_index().rename(columns={COL_REGION: 'country'}))
        df_plot_geo = pd.merge(world, df_plot, on='country', how='left')

        df_plot_geo = df_plot_geo[((df_plot_geo['Cases.total'] >= cases_filter)
                                   | (df_plot_geo['Deaths.total'] >= deaths_filter))]
        return df_plot_geo

    @classmethod
    def make_map_figure(cls,
                        df_plot_geo,
                        col,
                        colorbar_title,
                        subtitle,
                        err_col=None,
                        hover_text_func=None,
                        scale_max=None,
                        colorscale='Bluered',
                        ):
        import plotly.graph_objects as go

        # hover text
        hover_text_func = hover_text_func if callable(hover_text_func) else lambda r: ''
        df_plot_geo['text'] = df_plot_geo.apply(hover_text_func, axis=1)

        percent = ('rate' in col or 'ratio' in col)

        fig = go.FigureWidget(
            data=go.Choropleth(
                locations=df_plot_geo.index,
                geojson=df_plot_geo['geometry'].__geo_interface__,
                z=df_plot_geo[col].fillna(float('nan')) * (100 if percent else 1),
                zmin=0,
                zmax=scale_max,
                text=df_plot_geo['text'],
                ids=df_plot_geo['country'],
                customdata=cls.error_series_to_string_list(
                    series=df_plot_geo[col],
                    err_series=df_plot_geo[err_col] if err_col else None,
                    percent=percent
                ),
                hovertemplate="<b>%{id}</b>:<br><b>%{z:.1f}%{customdata}</b><br>%{text}<extra></extra>",
                colorscale=colorscale,
                colorbar={'title': {'text': f'<b>{colorbar_title}</b>'}},
                autocolorscale=False,
                marker_line_color='#9fa8ad',
                marker_line_width=0.5,
            ))

        fig.update_layout(
            title={'text': f"<b>Map of</b>: {subtitle}", 'y': 0.875, 'x': 0.005},
            annotations=[
                dict(text="Map<br>choice:", showarrow=False, x=0.005, y=1.075, yref="paper", align="left")
            ],
            width=800,
            height=450,
            autosize=True,
            margin=dict(t=0, b=0, l=0, r=0),
            template="plotly_white",
            hoverlabel=dict(font_size=12),
            geo=dict(
                showframe=False,
                projection_type='natural earth',
                resolution=110,
                showcoastlines=True, coastlinecolor="#c4cace",
                showland=True, landcolor="#d8d8d8",
                showocean=True, oceancolor="#d2e9f7",
                showlakes=True, lakecolor="#d2e9f7",
                fitbounds="locations"
            )
        )
        return fig

    @staticmethod
    def error_series_to_string_list(series, err_series=None, percent=False):
        percent_str = ('%' if percent else '')
        if err_series is None:
            return [percent_str] * len(series)
        else:
            return (percent_str + ' ± ' +
                    (err_series * (100 if percent else 1)).apply('{:.1f}'.format) +
                    percent_str
                    ).to_list()

    @classmethod
    def button_dict(cls, series, title, colorscale, scale_max=None,
                    percent=False, subtitle=None, err_series=None,
                    hover_text_list=None, colorbar_title=None):
        import plotly.express as px

        series = series.fillna(float('nan'))
        series *= 100 if percent else 1
        subtitle = subtitle if subtitle is not None else title.replace('<br>', ' ')

        scale_obj = getattr(px.colors.sequential, colorscale)
        scale_arg = [[(i - 1) / (len(scale_obj) - 1), c]
                     for i, c in enumerate(scale_obj, start=1)]

        max_arg = series.max() if scale_max is None else min(scale_max, series.max())

        data_args_dict = {
            'z': [series.to_list()],
            'zmax': [max_arg],
            'colorbar': [{'title': {'text': f'<b>{colorbar_title or title}</b>'}}],
            'colorscale': [scale_arg],
            'customdata': [cls.error_series_to_string_list(
                series, err_series=err_series, percent=percent)]
        }

        if hover_text_list:
            data_args_dict['text'] = [hover_text_list]

        return dict(args=[data_args_dict,
                          {'title': {'text': f"<b>Map of</b>: {subtitle}",
                                     'y': 0.875, 'x': 0.005}}
                          ],
                    label=title,
                    method="update")
