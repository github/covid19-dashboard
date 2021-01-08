# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.4.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# # World News from data (good & bad)
# > Significant changes vs. 10 days ago in transmission rates, ICU demand, and cases & deaths data.
#
# - categories: [world, overview, interactive, news]
# - permalink: /covid-news/
# - author: <a href=https://github.com/artdgn/>artdgn</a>
# - toc: true
# - image: images/news.png
# - hide: false

# > Warning: This dashboard was not built by an epidemiologist.

# > Note: Click a country name to open a search results page for that country's COVID-19 news.

# +
#hide
import pandas as pd
import covid_helpers as covid_helpers

stylers = covid_helpers.PandasStyling

# +
#hide
day_diff = 10

cur_data = covid_helpers.CovidData()
df_cur_all, debug_dfs = cur_data.table_with_projections(projection_days=[30], debug_dfs=True)
df_cur = cur_data.filter_df(df_cur_all)

past_data = covid_helpers.CovidData(-day_diff)
df_past = past_data.filter_df(past_data.table_with_projections(projection_days=[day_diff-1]))
# -

#hide_input
from IPython.display import Markdown
past_date = pd.to_datetime(past_data.dt_cols[-1]).date().isoformat()
Markdown(f"***Based on data up to: {cur_data.cur_date}. \
            Compared to ({day_diff} days before): {past_date}***")


# +
#hide
df_data = df_cur.copy()
df_data['transmission_rate_past'] = df_past['transmission_rate']
df_data['transmission_rate_std_past'] = df_past['transmission_rate_std']
df_data['needICU.per100k_past'] = df_past['needICU.per100k']

# deaths toll changes
df_data['Deaths.total.diff'] = df_data['Deaths.total'] - df_past['Deaths.total']
df_data['Deaths.new.per100k.past'] = df_past['Deaths.new.per100k']
df_data['Deaths.new.past'] = df_past['Deaths.new']
df_data['Deaths.diff.per100k'] = df_data['Deaths.total.diff'] / (df_data['population'] / 1e5)

# misses and explanations
df_data['transmission_rate.change'] = (df_data['transmission_rate'] / df_data['transmission_rate_past']) - 1
df_data['affected_ratio.miss'] = (df_cur['affected_ratio.est'] / df_past['affected_ratio.est.+9d']) - 1
df_data['needICU.per100k.miss'] = (df_cur['needICU.per100k'] / df_past['needICU.per100k.+9d']) - 1
df_data['testing_bias.change'] = (df_data['current_testing_bias'] / df_past['current_testing_bias']) - 1

# -


#hide
def emoji_flags(inds):
    return ' '.join(df_cur.loc[inds]['emoji_flag'])


# # Transmission rate:
# > Note: "transmission rate" here is a measure of speed of spread of infection, and means how much of the susceptible population each infected person is infecting per day (if everyone is susceptible). E.g. 10% means that 100 infected patients will infect 10 new people per day. Related to [R0](https://en.wikipedia.org/wiki/Basic_reproduction_number). See [Methodology](#Methodology) for details of calculation.

# hide
def style_news_infections(df):
    cols = {
        'transmission_rate': '<i>Current:</i><br>Estimated<br>daily<br>transmission<br>rate',
        'transmission_rate_past': f'<i>{day_diff} days ago:</i><br>Estimated<br>daily<br>transmission<br>rate',
        'Cases.new.est': 'Estimated <br> <i>recent</i> cases <br> in last 5 days',
        'needICU.per100k': 'Estimated<br>current<br>ICU need<br>per 100k<br>population',
        'affected_ratio.est': 'Estimated <br><i>total</i><br>affected<br>population<br>percentage',
    }

    rate_norm = max(df['transmission_rate'].max(), df['transmission_rate_past'].max())
    df_show = stylers.country_index_emoji_link(df)[cols.keys()].rename(columns=cols)
    return (df_show.style
            .bar(subset=[cols['needICU.per100k']], color='#b21e3e', vmin=0, vmax=10)
            .bar(subset=cols['Cases.new.est'], color='#b57b17', vmin=0)
            .bar(subset=cols['affected_ratio.est'], color='#5dad64', vmin=0, vmax=1.0)
            .apply(stylers.add_bar, color='#f49d5a',
                   s_v=df['transmission_rate'] / rate_norm, subset=cols['transmission_rate'])
            .apply(stylers.add_bar, color='#d8b193',
                   s_v=df['transmission_rate_past'] / rate_norm,
                   subset=cols['transmission_rate_past'])
            .format('<b>{:.2f}</b>', subset=[cols['needICU.per100k']])
            .format('<b>{:,.0f}</b>', subset=cols['Cases.new.est'])
            .format('<b>{:.1%}</b>', subset=[cols['affected_ratio.est'],
                                             cols['transmission_rate'],
                                             cols['transmission_rate_past']], na_rep="-"))


# hide
rate_diff = df_data['transmission_rate'] - df_data['transmission_rate_past']
higher_trans = (
        (df_data['Cases.new.est'] > 100) &
        (rate_diff > 0.02) &
        (rate_diff > df_data['transmission_rate_std_past']) &
        (df_data['transmission_rate_past'] != 0)  # countries reporting infrequently
)
new_waves = rate_diff[higher_trans].sort_values(ascending=False).index

# hide_input
Markdown(f"## &#11093; Bad news: new waves {emoji_flags(new_waves)}")

# > Large increase in transmission rate vs. 10 days ago, that might mean a relapse, new wave, worsening outbreak.
#
# - Countries are sorted by size of change in transmission rate.
# - Includes only countries that were previously active (more than 100 estimated new cases).
# - "Large increase" = at least +2% change.

# hide_input
style_news_infections(df_data.loc[new_waves])

# +
# hide
df_alt_all = pd.concat([d.reset_index() for d in debug_dfs], axis=0)
def infected_plots(countries, title):
    return covid_helpers.altair_multiple_countries_infected(
        df_alt_all, countries=countries, title=title, marker_day=day_diff)


# -

# > Tip: Click country name in legend to switch countries. Uze mouse wheel to zoom Y axis.

#hide_input
infected_plots(new_waves, "Countries with new waves (vs. 10 days ago)")

#hide
lower_trans = (
        (rate_diff < -0.02) &
        (df_cur['Cases.new.est'] > 100) &
        (rate_diff.abs() > df_data['transmission_rate_std']) &
        (df_data['transmission_rate'] != 0)  # countries reporting infrequently
)
slowing_outbreaks = rate_diff[lower_trans].sort_values().index

#hide_input
Markdown(f"## &#128994; Good news: slowing waves {emoji_flags(slowing_outbreaks)}")

# > Large decrease in transmission rate vs. 10 days ago, that might mean a slowing down / effective control measures.
#
# - Countries are sorted by size of change in transmission rate.
# - Includes only countries that were previously active (more than 100 estimated new cases).
# - "Large decrease" = at least -2% change.

#hide_input
style_news_infections(df_data.loc[slowing_outbreaks])

# > Tip: Click country name in legend to switch countries. Uze mouse wheel to zoom Y axis.

#hide_input
infected_plots(slowing_outbreaks, "Countries with slowing waves (vs. 10 days ago)")

# # ICU need

# hide
def style_news_icu(df):
    cols = {
        'needICU.per100k': '<i>Current:</i><br>Estimated<br>ICU need<br>per 100k<br>population',
        'needICU.per100k_past': f'<i>{day_diff} days ago:</i><br>Estimated<br>ICU need<br>per 100k<br>population',
        'Cases.new.est': 'Estimated<br><i>recent</i> cases<br> in last 5 days',
        'transmission_rate': 'Estimated<br>daily<br>transmission<br>rate',
        'affected_ratio.est': 'Estimated <br><i>total</i><br>affected<br>population<br>percentage',
      }

    df_show = stylers.country_index_emoji_link(df)[cols.keys()].rename(columns=cols)
    return (df_show.style
        .bar(subset=cols['needICU.per100k'], color='#b21e3e', vmin=0, vmax=10)
        .bar(subset=cols['needICU.per100k_past'], color='#c67f8e', vmin=0, vmax=10)
        .bar(subset=cols['Cases.new.est'], color='#b57b17', vmin=0)
        .bar(subset=cols['affected_ratio.est'], color='#5dad64', vmin=0, vmax=1.0)
        .apply(stylers.add_bar, color='#f49d5a',
               s_v=df['transmission_rate']/df['transmission_rate'].max(),
               subset=cols['transmission_rate'])
        .format('<b>{:.2f}</b>', subset=[cols['needICU.per100k'], cols['needICU.per100k_past']])
        .format('<b>{:,.0f}</b>', subset=cols['Cases.new.est'])
        .format('<b>{:.1%}</b>', subset=[cols['affected_ratio.est'],
                                         cols['transmission_rate']]))


# hide
icu_diff = df_cur['needICU.per100k'] - df_past['needICU.per100k']
icu_increase = icu_diff[icu_diff > 0.2].sort_values(ascending=False).index

# hide_input
Markdown(f"## &#11093; Bad news: higher ICU need {emoji_flags(icu_increase)}")

# > Large increases in need for ICU beds per 100k population vs. 10 days ago.
#
# - Only countries for which the ICU need increased by more than 0.2 (per 100k).

# hide_input
style_news_icu(df_data.loc[icu_increase])

# > Tip: Click country name in legend to switch countries. Uze mouse wheel to zoom Y axis.

# hide_input
infected_plots(icu_increase, "Countries with Higher ICU need (vs. 10 days ago)")

# hide
icu_decrease = icu_diff[icu_diff < -0.1].sort_values().index

# hide_input
Markdown(f"## &#128994; Good news: lower ICU need {emoji_flags(icu_decrease)}")


# > Large decreases in need for ICU beds per 100k population vs. 10 days ago.
#
# - Only countries for which the ICU need decreased by more than 0.1 (per 100k).

# hide_input
style_news_icu(df_data.loc[icu_decrease])

# > Tip: Click country name in legend to switch countries. Uze mouse wheel to zoom Y axis.

# hide_input
infected_plots(icu_decrease, "Countries with Lower ICU need (vs. 10 days ago)")

# # New cases and deaths:

# hide
new_entries = df_cur.index[~df_cur.index.isin(df_past.index)]

# hide_input
Markdown(f"## &#11093; Bad news: new first significant outbreaks {emoji_flags(new_entries)}")

# > Countries that have started their first significant outbreak (crossed 1000 total reported cases or 20 deaths) vs. 10 days ago.

# hide_input
style_news_infections(df_data.loc[new_entries])

# > Tip: Click country name in legend to switch countries. Uze mouse wheel to zoom Y axis.

# hide_input
infected_plots(new_entries, "Countries with first large outbreak (vs. 10 days ago)")


# hide
def style_no_news(df):
    cols = {
        'Cases.total.est': 'Estimated<br>total<br>cases',
        'Deaths.total': 'Total<br>reported<br>deaths',
        'last_case_date': 'Date<br>of last<br>reported case',
        'last_death_date': 'Date<br>of last<br>reported death',
      }
    df_show = stylers.country_index_emoji_link(df)[cols.keys()].rename(columns=cols)
    return (df_show.style
        .format('<b>{:,.0f}</b>', subset=[cols['Cases.total.est'], cols['Deaths.total']]))


#hide
significant_past = ((df_past['Cases.total.est'] > 1000) & (df_past['Deaths.total'] > 10))
active_in_past = ((df_past['Cases.new'] > 0) | (df_past['Deaths.new'] > 0))
no_cases_filt = ((df_cur['Cases.total'] - df_past['Cases.total']) == 0)
no_deaths_filt = ((df_cur['Deaths.total'] - df_past['Deaths.total']) == 0)
no_cases_and_deaths = df_cur.loc[no_cases_filt & no_deaths_filt &
                                 significant_past & active_in_past].index

# hide_input
Markdown(f"## &#128994; Good news: no new cases or deaths {emoji_flags(no_cases_and_deaths)}")

# > New countries with no new cases or deaths vs. 10 days ago.
#
# - Only considering countries that had at least 1000 estimated total cases and at least 10 total deaths and had an active outbreak previously.

# hide_input
style_no_news(df_data.loc[no_cases_and_deaths])

# > Tip: Click country name in legend to switch countries. Uze mouse wheel to zoom Y axis.

# hide_input
infected_plots(no_cases_and_deaths, "New countries with no new cases or deaths (vs. 10 days ago)")

# hide
no_deaths = df_cur.loc[no_deaths_filt & (~no_cases_filt) &
                       significant_past & active_in_past].index

# hide_input
Markdown(f"## Mixed news: no new deaths, only new cases {emoji_flags(no_deaths)}")

# > New countries with no new deaths (only new cases) vs. 10 days ago.
#
# - Only considering countries that had at least 1000 estimated total cases and at least 10 total deaths and had an active outbreak previously.

# hide_input
style_news_infections(df_data.loc[no_deaths])

# > Tip: Click country name in legend to switch countries. Uze mouse wheel to zoom Y axis.

# hide_input
infected_plots(no_deaths, "Countries with only new cases (vs. 10 days ago)")

# hide
not_active = df_cur.loc[no_cases_filt & significant_past & ~active_in_past].index

# hide_input
Markdown(f"## No news: continously inactive countries {emoji_flags(not_active)}")

# > Countries that had no new cases or deaths 10 days ago or now.
#
# - Only considering countries that had at least 1000 estimated total cases and at least 10 total deaths.
# - Caveat:  these countries may have stopped reporting data like [Tanzania](https://en.wikipedia.org/wiki/COVID-19_pandemic_in_Tanzania).

# hide_input
style_no_news(df_data.loc[not_active])

# > Tip: Click country name in legend to switch countries. Uze mouse wheel to zoom Y axis.

# hide_input
infected_plots(not_active, "Continuosly inactive countries (now and 10 days ago)")


# # Deaths burden:

# hide
def style_death_burden(df):
    cols = {
        'Deaths.new.per100k': f'<i>Current</i>:<br>{cur_data.PREV_LAG} day<br>death<br>burden<br>per 100k',
        'Deaths.new.per100k.past': f'<i>{day_diff} days ago</i>:<br>{cur_data.PREV_LAG} day<br>death<br>burden<br>per 100k',
        'Deaths.total.diff': f'New<br>reported deaths<br>since {day_diff}<br>days ago',
        'needICU.per100k': 'Estimated<br>current<br>ICU need<br>per 100k<br>population',
        'affected_ratio.est': 'Estimated <br><i>total</i><br>affected<br>population<br>percentage',
    }
    df_show = stylers.country_index_emoji_link(df)[cols.keys()].rename(columns=cols)
    death_norm = max(df['Deaths.new.per100k'].max(), df['Deaths.new.per100k.past'].max())
    return (df_show.style
            .bar(subset=cols['needICU.per100k'], color='#b21e3e', vmin=0, vmax=10)
            .bar(subset=cols['Deaths.new.per100k'], color='#7b7a7c', vmin=0, vmax=death_norm)
            .bar(subset=cols['Deaths.new.per100k.past'], color='#918f93', vmin=0, vmax=death_norm)
            .bar(subset=cols['Deaths.total.diff'], color='#6b595d', vmin=0)
            .bar(subset=cols['affected_ratio.est'], color='#5dad64', vmin=0, vmax=1.0)
            .format('<b>{:.0f}</b>', subset=[cols['Deaths.total.diff'],
                                             ])
            .format('<b>{:.1f}</b>', subset=cols['needICU.per100k'])
            .format('<b>{:.2f}</b>', subset=[cols['Deaths.new.per100k'],
                                             cols['Deaths.new.per100k.past']])
            .format('<b>{:.1%}</b>', subset=[cols['affected_ratio.est']], na_rep="-"))


# hide
death_change_ratio = df_data['Deaths.new.per100k'] / df_data['Deaths.new.per100k.past']
filt = (
    (df_data['Deaths.new'] > 10) &
    (df_data['Deaths.new.past'] > 10) &
    (df_data['Deaths.new.per100k'] > 0.1) &
    (death_change_ratio > 2))
higher_death_burden = df_data[filt]['Deaths.diff.per100k'].sort_values(ascending=False).index

# hide_input
Markdown(f"## &#11093; Bad news: higher death burden {emoji_flags(higher_death_burden)}")

# > Countries with significantly higher recent death burden per 100k population vs. 10 days ago.
#
# - "Significantly higher" = 100% more.
# - Only considering countries that had at least 10 recent deaths in both timeframes, and death burden of at least 0.1 per 100k.

# hide_input
style_death_burden(df_data.loc[higher_death_burden])

# hide_input
infected_plots(higher_death_burden, "Countries with higher death burden (vs. 10 days ago)")

# hide
filt = (
    (df_data['Deaths.new'] > 10) &
    (df_data['Deaths.new.past'] > 10) &
    (df_data['Deaths.new.per100k.past'] > 0.1) &
    (death_change_ratio < 0.5))
lower_death_burden = df_data[filt]['Deaths.diff.per100k'].sort_values(ascending=False).index

# hide_input
Markdown(f"## &#128994; Good news: lower death burden {emoji_flags(lower_death_burden)}")

# > Countries with significantly lower recent death burden per 100k population vs. 10 days ago.
#
# - "Significantly lower" = 50% less
# - Only considering countries that had at least 10 recent deaths in both timeframes, and death burden of at least 0.1 per 100k.

# hide_input
style_death_burden(df_data.loc[lower_death_burden])

# hide_input
infected_plots(lower_death_burden, "Countries with lower death burden (vs. 10 days ago)")

# # Appendix:

# > Note: For interactive map, per country details, projections, and modeling methodology see [Projections of ICU need by Country dashboard](/covid-progress-projections/)

# > Warning: the visualisation below contains the results of a predictive model that was not built by an epidemiologist.

# ## Future model projections plots per country
# > For countries in any of the above groups.

# > Tip: Choose country from the drop-down below the graph.

#hide_input
all_news = (new_waves, slowing_outbreaks, 
            icu_increase, icu_decrease,
            higher_death_burden, lower_death_burden,
            not_active, no_deaths, no_cases_and_deaths, new_entries)
news_countries = [c for g in all_news for c in g]
df_alt_filt = df_alt_all[(df_alt_all['day'] > -60) & 
                         (df_alt_all['country'].isin(news_countries))]
covid_helpers.altair_sir_plot(df_alt_filt, new_waves[0])

#hide
df_tot = df_alt_all.rename(columns={'country': cur_data.COL_REGION}
                          ).set_index(cur_data.COL_REGION)
df_tot['population'] = df_cur_all['population']
for c in df_tot.columns[df_alt_all.dtypes == float]:
    df_tot[c + '-total'] = df_tot[c] * df_tot['population']
df_tot = df_tot.reset_index()
df_tot.columns = [c.replace('.', '-') for c in df_tot.columns]

#hide_input
df_now = df_tot[df_tot['day'] == 0]
pop = df_now['population'].sum()
s_now = df_now['Susceptible-total'].sum() / pop
i_now = df_now['Infected-total'].sum() / pop
r_now = df_now['Removed-total'].sum() / pop
Markdown("## World totals:\n"
         f"Infected &#128567;: **{i_now:.1%}**, "
         f"Removed &#128532;: **{r_now:.1%}**, "
         f"Susceptible &#128543;: **{s_now:.1%}**")

# ## Future World projections (all countries stacked)
# The outputs of the models for all countries in stacked plots.
# > Tip: Hover the mouse of the area to see which country is which and the countries S/I/R ratios at that point.
#
# > Tip: The plots are zoomable and draggable.

# +
#hide
# filter by days
days = 30
df_tot = df_tot[df_tot['day'].between(-days, days) | (df_tot['day'] % 10 == 0)]

# filter out noisy countries for actively infected plot:
df_tot_filt = df_tot[df_tot[cur_data.COL_REGION].isin(df_cur.index.unique())]
# -

# ### World total estimated actively infected

# +
#hide_input
import altair as alt
alt.data_transformers.disable_max_rows()

# today
today_line = (alt.Chart(pd.DataFrame({'x': [0]}))
                  .mark_rule(color='orange')
                  .encode(x='x', size=alt.value(1)))

# make plot
max_y = (df_tot_filt[df_tot_filt['day'].between(-days, days)]
         .groupby('day')['Infected-total'].sum().max())
stacked_inf = alt.Chart(df_tot_filt).mark_area().encode(
    x=alt.X('day:Q',
            title=f'days relative to today ({cur_data.cur_date})',
            scale=alt.Scale(domain=(-days, days))),
    y=alt.Y("Infected-total:Q", stack=True, title="Number of people",
           scale=alt.Scale(domain=(0, max_y))),
    color=alt.Color("Country/Region:N", legend=None),
    tooltip=['Country/Region', 'Susceptible', 'Infected', 'Removed'],    
)
(stacked_inf + today_line).interactive()\
.properties(width=650, height=340)\
.properties(title='Actively infected')\
.configure_title(fontSize=20)
# -

# ### World total estimated recovered or dead

# +
#hide_input
max_y = df_tot_filt[df_tot_filt['day']==days]['Removed-total'].sum()
stacked_rem = alt.Chart(df_tot_filt).mark_area().encode(
    x=alt.X('day:Q',
            title=f'days relative to today ({cur_data.cur_date})',
            scale=alt.Scale(domain=(-days, days))),
    y=alt.Y("Removed-total:Q", stack=True, title="Number of people",
           scale=alt.Scale(domain=(0, max_y))),
    color=alt.Color("Country/Region:N", legend=None),
    tooltip=['Country/Region', 'Susceptible', 'Infected', 'Removed']
)

(stacked_rem + today_line).interactive()\
.properties(width=650, height=340)\
.properties(title='Recovered or dead')\
.configure_title(fontSize=20)
# -

# <a id='methodology'></a>
# ## Methodology
# - I'm not an epidemiologist. This is an attempt to understand what's happening, and what the future looks like if current trends remain unchanged.
# - Everything is approximated and depends heavily on underlying assumptions.
# - Transmission rate calculation:
#     - Growth rate is calculated over the 5 past days by averaging the daily growth rates.
#     - Confidence bounds are calculated from the weighted standard deviation of the growth rate over the last 5 days. Model predictions are calculated for growth rates within 1 STD of the weighted mean. The maximum and minimum values for each day are used as confidence bands.
# Countries with highly noisy transmission rates are exluded from tranmission rate change tables ("new waves", "slowing waves").
#     - Transmission rate, and its STD are calculated from growth rate and its STD using active cases estimation.
#     - For projections (into future) very noisy projections (with broad confidence bounds) are not shown in the tables.
#     - Where the rate estimated from [Total Outstanding Cases](https://covid19dashboards.com/outstanding_cases/#Appendix:-Methodology-of-Predicting-Recovered-Cases) is too high (on down-slopes) recovery probability if 1/20 is used (equivalent 20 days to recover).
# - Total cases are estimated from the reported deaths for each country:
#     - Each country has a different testing policy and capacity and cases are under-reported in some countries. Using an estimated IFR (fatality rate) we can estimate the number of cases some time ago by using the total deaths until today.
#     - IFRs for each country is estimated using the age adjusted IFRs from [May 1 New York paper](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3590771) and [UN demographic data for 2020](https://population.un.org/wpp/Download/Standard/Population/). These IFRs can be found in `df['age_adjusted_ifr']` column. Some examples: US - 0.98%, UK - 1.1%, Qatar - 0.25%, Italy - 1.4%, Japan - 1.6%.
#     - The average fatality lag is assumed to be 8 days on average for a case to go from being confirmed positive (after incubation + testing lag) to death. This is the same figure used by ["Estimating The Infected Population From Deaths"](https://covid19dashboards.com/covid-infected/).
#     - Testing bias adjustment: the actual lagged fatality rate is than divided by the IFR to estimate the testing bias in a country. The estimated testing bias then multiplies the reported case numbers to estimate the *true* case numbers (*=case numbers if testing coverage was as comprehensive as in the heavily tested countries*).
# - ICU need is calculated and age-adjusted as follows:
#     - UK ICU ratio was reported as [4.4% of active reported cases](https://www.imperial.ac.uk/media/imperial-college/medicine/sph/ide/gida-fellowships/Imperial-College-COVID19-NPI-modelling-16-03-2020.pdf).
#     - Using UKs ICU ratio, UK's testing bias, and IFRs corrected for age demographics we can estimate each country's ICU ratio (the number of cases requiring ICU hospitalisation).
# ![](https://artdgn.goatcounter.com/count?p=c19d-news)
