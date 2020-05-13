import os
from urllib import request

import numpy as np
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


class WordPopulation:
    csv_path = os.path.join(data_folder, 'world_population.csv')
    page = 'https://www.worldometers.info/world-population/population-by-country/'
    # alternative https://en.wikipedia.org/wiki/List_of_countries_by_population_%28United_Nations%29 table 5

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


class OverviewData:
    COL_REGION = 'Country/Region'
    ABS_COLS = ['Cases.total', 'Deaths.total', 'Cases.new', 'Deaths.new']

    PER_100K_COLS = [f'{c}.per100k' for c in ABS_COLS]
    CASES_COLS = ABS_COLS[::2] + PER_100K_COLS[::2]
    EST_COLS = [f'{c}.est' for c in CASES_COLS]

    dft_cases = SourceData.get_covid_dataframe('confirmed')
    dft_deaths = SourceData.get_covid_dataframe('deaths')
    dft_recovered = SourceData.get_covid_dataframe('recovered')
    LAST_DATE_I, dt_cols = SourceData.get_dates(dft_cases)

    dt_today = dt_cols[LAST_DATE_I]
    dfc_cases = dft_cases.groupby(COL_REGION)[dt_today].sum()
    dfc_deaths = dft_deaths.groupby(COL_REGION)[dt_today].sum()

    PREV_LAG = 5
    dt_lag = dt_cols[LAST_DATE_I - PREV_LAG]

    # modeling constants
    ## testing bias
    death_lag = 8
    # additional updated data with discussions about CFRs:
    # https://www.cebm.net/covid-19/global-covid-19-case-fatality-rates/
    cfr_lower_bound = 0.0072

    ## recovery estimation
    recovery_lagged9_rate = 0.07
    ## sir model
    rec_rate_simple = 0.05
    ## icu need estimation
    ## https://www.imperial.ac.uk/media/imperial-college/medicine/sph/ide/gida-fellowships/Imperial-College-COVID19-NPI-modelling-16-03-2020.pdf
    ## 4.4% serious symptomatic cases
    ICU_ratio = 0.044
    ## ICU spare capacity
    # occupancy 66% for us:
    #   https://www.sccm.org/Blog/March-2020/United-States-Resource-Availability-for-COVID-19
    # occupancy average 75% for OECD:
    #   https://www.oecd-ilibrary.org/social-issues-migration-health/health-at-a-glance-2019_4dd50c09-en
    icu_spare_capacity_ratio = 0.3

    @classmethod
    def lagged_cases(cls, lag=PREV_LAG):
        return cls.dft_cases.groupby(cls.COL_REGION)[cls.dt_cols[cls.LAST_DATE_I - lag]].sum()

    @classmethod
    def lagged_deaths(cls, lag=PREV_LAG):
        return cls.dft_deaths.groupby(cls.COL_REGION)[cls.dt_cols[cls.LAST_DATE_I - lag]].sum()

    @classmethod
    def overview_table(cls):
        df_table = (pd.DataFrame({'Cases.total': cls.dfc_cases,
                                  'Deaths.total': cls.dfc_deaths,
                                  'Cases.total.prev': cls.lagged_cases(),
                                  'Deaths.total.prev': cls.lagged_deaths()})
                    .sort_values(by=['Cases.total', 'Deaths.total'], ascending=[False, False])
                    .reset_index())
        df_table.rename(columns={'index': 'Country/Region'}, inplace=True)
        for c in cls.ABS_COLS[:2]:
            df_table[c.replace('total', 'new')] = (df_table[c] - df_table[f'{c}.prev']).clip(0)  # DATA BUG
        df_table['Fatality Rate'] = (100 * df_table['Deaths.total'] / df_table['Cases.total']).round(1)
        df_table['Continent'] = df_table['Country/Region'].map(SourceData.mappings['map.continent'])

        # remove problematic
        df_table = df_table[~df_table['Country/Region'].isin(['Cape Verde', 'Cruise Ship', 'Kosovo'])]
        return df_table

    @classmethod
    def make_new_cases_arrays(cls, n_days=50):
        dft_ct_cases = cls.dft_cases.groupby(cls.COL_REGION)[cls.dt_cols].sum()
        dft_ct_new_cases = dft_ct_cases.diff(axis=1).fillna(0).astype(int)
        return dft_ct_new_cases.loc[:, cls.dt_cols[cls.LAST_DATE_I - n_days]:cls.dt_cols[cls.LAST_DATE_I]]

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
              .drop(['Cases.total.prev', 'Deaths.total.prev'], axis=1)
              .set_index(cls.COL_REGION, drop=True)
              .sort_values('Cases.new', ascending=False))
        df['Fatality Rate'] /= 100

        df_pop = cls.populations_df()

        df['population'] = df_pop['population']
        df.dropna(subset=['population'], inplace=True)

        for col, per_100k_col in zip(cls.ABS_COLS, cls.PER_100K_COLS):
            df[per_100k_col] = df[col] * 1e5 / df['population']

        return df

    @classmethod
    def table_with_estimated_cases(cls):
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

        lagged_mortality_rate = (cls.dfc_deaths + 1) / (cls.lagged_cases(cls.death_lag) + 1)
        testing_bias = lagged_mortality_rate / cls.cfr_lower_bound
        testing_bias[testing_bias < 1] = 1

        df = cls.overview_table_with_per_100k()
        df['lagged_fatality_rate'] = lagged_mortality_rate
        df['testing_bias'] = testing_bias

        for col, est_col in zip(cls.CASES_COLS, cls.EST_COLS):
            df[est_col] = df['testing_bias'] * df[col]

        return df.sort_values('Cases.new.est', ascending=False)

    @classmethod
    def smoothed_growth_rates(cls, n_days):
        recent_dates = cls.dt_cols[-n_days:]

        cases = (cls.dft_cases.groupby(cls.COL_REGION).sum()[recent_dates] + 1)  # with pseudo counts

        diffs = cls.dft_cases.groupby(cls.COL_REGION).sum().diff(axis=1)[recent_dates]

        cases, diffs = cases.T, diffs.T  # broadcasting works correctly this way

        # daily rate is new / (total - new)
        daily_growth_rates = cases / (cases - diffs)

        # dates with larger number of cases have higher sampling accuracy
        # so their measurement deserve more confidence
        sampling_weights = (cases / cases.sum(0))

        weighted_mean = (daily_growth_rates * sampling_weights).sum(0)

        weighted_std = ((daily_growth_rates - weighted_mean).pow(2) *
                        sampling_weights).sum(0).pow(0.5)

        return weighted_mean, weighted_std

    @classmethod
    def table_with_icu_capacities(cls):
        df = cls.table_with_estimated_cases()

        df_beds = cls.beds_df()

        df['icu_capacity_per100k'] = df_beds['icu_per_100k']

        df['icu_spare_capacity_per100k'] = df['icu_capacity_per100k'] * cls.icu_spare_capacity_ratio
        return df

    @classmethod
    def table_with_projections(cls, projection_days=(7, 14, 30, 60, 90), debug_dfs=False):
        df = cls.table_with_icu_capacities()

        df['affected_ratio'] = df['Cases.total'] / df['population']

        past_active, past_recovered = cls._calculate_recovered_and_active_until_now(df)

        df, traces = cls._run_model_forward(
            df,
            past_active=past_active.copy(),
            past_recovered=past_recovered.copy(),
            projection_days=projection_days)

        if debug_dfs:
            debug_dfs = cls._SIR_timeseries_for_countries(
                debug_countries=df.index,
                traces=traces,
                simulation_start_day=len(past_recovered) - 1,
                growth_rate=df['growth_rate'])
            return df, debug_dfs
        return df

    @classmethod
    def _calculate_recovered_and_active_until_now(cls, df):
        # estimated daily cases ratio of population
        lagged_cases_ratios = (cls.dft_cases.groupby(cls.COL_REGION).sum()[cls.dt_cols].T *
                               df['testing_bias'].T / df['population'].T).T
        # protect from testing bias over-inflation
        lagged_cases_ratios[lagged_cases_ratios > 1] = 1

        # run through history and estimate recovered and active using:
        # https://covid19dashboards.com/outstanding_cases/#Appendix:-Methodology-of-Predicting-Recovered-Cases
        actives, recs = [], []
        zeros_series = lagged_cases_ratios[cls.dt_cols[0]] * 0  # this is to have consistent types
        for day in range(len(cls.dt_cols)):
            prev_rec = recs[day - 1] if day > 0 else zeros_series
            tot_lagged_9 = lagged_cases_ratios[cls.dt_cols[day - 9]] if day >= 8 else zeros_series
            new_recs = prev_rec + (tot_lagged_9 - prev_rec) * cls.recovery_lagged9_rate
            new_recs[new_recs > 1] = 1
            recs.append(new_recs)
            actives.append(lagged_cases_ratios[cls.dt_cols[day]] - new_recs)

        return actives, recs

    @classmethod
    def _run_model_forward(cls,
                           df,
                           past_active,
                           past_recovered,
                           projection_days,
                           ):

        cur_growth_rate, growsth_rate_std = cls.smoothed_growth_rates(n_days=cls.PREV_LAG)
        df['growth_rate'] = (cur_growth_rate - 1)
        df['growth_rate_std'] = growsth_rate_std
        df['infection_rate'] = cls._growth_to_infection_rate(
            growth=cur_growth_rate, rec=past_recovered, act=past_active)

        sus, act, rec = cls.run_sir_mode(
            past_recovered, past_active, cur_growth_rate, n_days=projection_days[-1])

        # sample more growth rates
        sus_lists = [[s] for s in sus]
        act_lists = [[a] for a in act]
        rec_lists = [[r] for r in rec]

        for ratio in np.linspace(-1, 1, 10):
            pert_growth = cur_growth_rate + ratio * growsth_rate_std
            pert_growth[pert_growth < 0] = 0
            sus_other, act_other, rec_other = cls.run_sir_mode(
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
            icu_max = cls.ICU_ratio * 1e5 / df['testing_bias']
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
    def _growth_to_infection_rate(cls, growth, rec, act):
        daily_delta = growth - 1
        tot = rec[-1] + act[-1]
        active = act[-1]
        # Explanation of the formula below:
        #   daily delta = delta total / total
        #   daily delta = new-infected / total
        #   daily_delta = infect_rate * active * (1 - tot) / tot, so solving for infect_rate:
        infect_rate = (daily_delta * tot) / ((1 - tot) * active)
        return infect_rate

    @classmethod
    def run_sir_mode(cls, past_rec, past_act, growth, n_days):
        rec, act = past_rec.copy(), past_act.copy()

        infect_rate = cls._growth_to_infection_rate(growth, rec, act)

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

    @classmethod
    def _SIR_timeseries_for_countries(cls, debug_countries, traces,
                                      simulation_start_day, growth_rate):
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
                     for day in range(len(traces['rec_center']))
                     if day > simulation_start_day]

            title = (f"{debug_country}: "
                     f"Growth Rate: {growth_rate[debug_country]:.0%}. "
                     f"S/I/R init: {debug[0]['Susceptible']:.1%},"
                     f"{debug[0]['Infected']:.1%},{debug[0]['Removed']:.1%}")
            df = pd.DataFrame(debug).set_index('day')
            df['title'] = title
            df['country'] = debug_country
            dfs.append(df)
        return dfs

    @classmethod
    def filter_df(cls, df, cases_filter=1000, deaths_filter=20, population_filter=3e5):
        df = df.rename(index={'Bosnia and Herzegovina': 'Bosnia',
                              'United Arab Emirates': 'UAE'})
        return df[((df['Cases.total'] > cases_filter) |
                   (df['Deaths.total'] > deaths_filter)) &
                  (df['population'] > population_filter)][df.columns.sort_values()]


def pandas_console_options():
    pd.set_option('display.max_colwidth', 300)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)


def altair_sir_plot(df, default_country):
    import altair as alt

    alt.data_transformers.disable_max_rows()

    select_country = alt.selection_single(
        name='Select',
        fields=['country'],
        init={'country': default_country},
        bind=alt.binding_select(options=sorted(df['country'].unique()))
    )

    title = (alt.Chart(df[['country', 'title']].drop_duplicates())
             .mark_text(dy=-180, dx=0, size=16)
             .encode(text='title:N')
             .transform_filter(select_country))

    base = alt.Chart(df).encode(x='day:Q')

    line_cols = ['Infected', 'Susceptible', 'Removed']
    colors = ['red', 'blue', 'green']
    lines = (base.mark_line()
             .transform_fold(line_cols)
             .encode(x='day:Q',
                     y=alt.Y('value:Q',
                             axis=alt.Axis(format='%', title='Percentage of Population')),
                     color=alt.Color('key:N',
                                     scale=alt.Scale(domain=line_cols, range=colors))))

    import functools
    bands = functools.reduce(alt.Chart.__add__,
                             [base.mark_area(opacity=0.1, color=color)
                             .encode(y=f'{col}\.max:Q', y2=f'{col}\.min:Q')
                              for col, color in zip(line_cols, colors)])

    return ((lines + bands + title)
            .add_selection(select_country)
            .transform_filter(select_country)
            .configure_title(fontSize=20)
            .configure_axis(labelFontSize=15, titleFontSize=18, grid=True)
            .properties(width=550, height=340))


class PandasStyling:
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

        shapefile = 'data_files/110m_countries/ne_110m_admin_0_countries.shp'

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

        df_plot = (df_all.reset_index().rename(columns={'Country/Region': 'country'}))
        df_plot_geo = pd.merge(world, df_plot, on='country', how='left')

        df_plot_geo = df_plot_geo[((df_plot_geo['Cases.total'] >= cases_filter)
                                   | (df_plot_geo['Deaths.total'] >= deaths_filter))]
        return df_plot_geo

    @classmethod
    def make_map_figure(cls,
                        df_plot_geo,
                        col='needICU.per100k.+14d',
                        title='ICU need<br>(in 14 days)',
                        subtitle='Projected ICU need per 100k population in 14 days'):
        import plotly.graph_objects as go

        df_plot_geo['text'] = (df_plot_geo.apply(
            lambda r: (
                "<br>"
                f"Cases (reported): {r['Cases.total']:,.0f} (+<b>{r['Cases.new']:,.0f}</b>)<br>"
                f"Cases (estimated): {r['Cases.total.est']:,.0f} (+<b>{r['Cases.new.est']:,.0f}</b>)<br>"
                f"Affected percent: <b>{r['affected_ratio.est']:.1%}</b><br>"
                f"Infection rate: <b>{r['infection_rate']:.1%}</b> ± {r['growth_rate_std']:.1%}<br>"
                f"Deaths: {r['Deaths.total']:,.0f} (+<b>{r['Deaths.new']:,.0f}</b>)<br>"
            ), axis=1))

        fig = go.FigureWidget(
            data=go.Choropleth(
                locations=df_plot_geo['iso_code'],
                z=df_plot_geo[col].fillna(float('nan')),
                zmin=0,
                zmax=10,
                text=df_plot_geo['text'],
                ids=df_plot_geo['country'],
                customdata=cls.error_series_to_string_list(
                    series=df_plot_geo[col],
                    err_series=None if '+' not in col else df_plot_geo[col + '.err'],
                    percent=('rate' in col or 'ratio' in col)
                ),
                hovertemplate="<b>%{id}</b>:<br><b>%{z:.1f}%{customdata}</b><br>%{text}<extra></extra>",
                colorscale='sunsetdark',
                autocolorscale=False,
                marker_line_color='#9fa8ad',
                marker_line_width=0.5,
                colorbar_title=f'<b>{title}</b>',
            ))

        fig.update_layout(
            title={'text': f"<b>Map of</b>: {subtitle}", 'y': 0.875, 'x': 0.005},
            annotations=[
                dict(text="Data<br>choice:", showarrow=False, x=0.005, y=1.075, yref="paper", align="left")
            ],
            width=800,
            height=450,
            autosize=True,
            margin=dict(t=0, b=0, l=0, r=0),
            template="plotly_white",
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
                    percent=False, subtitle=None, err_series=None):
        import plotly.express as px

        series = series.fillna(float('nan'))
        series *= 100 if percent else 1
        subtitle = subtitle if subtitle is not None else title.replace('<br>', ' ')

        scale_obj = getattr(px.colors.sequential, colorscale)
        scale_arg = [[(i - 1) / (len(scale_obj) - 1), c]
                     for i, c in enumerate(scale_obj, start=1)]

        max_arg = series.max() if scale_max is None else min(scale_max, series.max())

        return dict(args=[
            {'z': [series.to_list()],
             'zmax': [max_arg],
             'colorbar': [{'title': {'text': f'<b>{title}</b>'}}],
             'colorscale': [scale_arg],
             'customdata': [cls.error_series_to_string_list(
                 series, err_series=err_series, percent=percent)]
             },
            {'title': {'text': f"<b>Map of</b>: {subtitle}",
                       'y': 0.875, 'x': 0.005}}],
            label=title, method="update")
