import pandas as pd
import numpy as np

def load_individual_timeseries(name):
    base_url='https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series'
    url = f'{base_url}/time_series_19-covid-{name}.csv'
    df = pd.read_csv(url, 
                     index_col=['Country/Region', 'Province/State', 'Lat', 'Long'])
    df['type'] = name.lower()
    df.columns.name = 'date'
    
    df = (df.set_index('type', append=True)
            .reset_index(['Lat', 'Long'], drop=True)
            .stack()
            .reset_index()
            .set_index('date')
         )
    df.index = pd.to_datetime(df.index)
    df.columns = ['country', 'state', 'type', 'cases']
    
    # Move HK to country level
    df.loc[df.state =='Hong Kong', 'country'] = 'Hong Kong'
    df.loc[df.state =='Hong Kong', 'state'] = np.nan
    
    # Aggregate large countries split by states
    df = pd.concat([df, 
                    (df.loc[~df.state.isna()]
                     .groupby(['country', 'date', 'type'])
                     .sum()
                     .rename(index=lambda x: x+' (total)', level=0)
                     .reset_index(level=['country', 'type']))
                   ])
    return df

def load_data(drop_states=False, p_crit=.05, filter_n_days_100=None):
    df = load_individual_timeseries('Confirmed')
    df = df.rename(columns={'cases': 'confirmed'})
    if drop_states:
        # Drop states for simplicity
        df = df.loc[df.state.isnull()]
        
    # Estimated critical cases
    df = df.assign(critical_estimate=df.confirmed*p_crit)

    # Compute days relative to when 100 confirmed cases was crossed
    df.loc[:, 'days_since_100'] = np.nan
    for country in df.country.unique():
        if not df.loc[(df.country == country), 'state'].isnull().all():
            for state in df.loc[(df.country == country), 'state'].unique():
                df.loc[(df.country == country) & (df.state == state), 'days_since_100'] = \
                    np.arange(-len(df.loc[(df.country == country) & (df.state == state) & (df.confirmed < 100)]), 
                              len(df.loc[(df.country == country) & (df.state == state) & (df.confirmed >= 100)]))
        else:
            df.loc[(df.country == country), 'days_since_100'] = \
                np.arange(-len(df.loc[(df.country == country) & (df.confirmed < 100)]), 
                          len(df.loc[(df.country == country) & (df.confirmed >= 100)]))

    # Add recovered cases
    df_recovered = load_individual_timeseries('Recovered')
    df_r = df_recovered.set_index(['country', 'state'], append=True)[['cases']]
    df_r.columns = ['recovered']

    # Add deaths
    df_deaths = load_individual_timeseries('Deaths')
    df_d = df_deaths.set_index(['country', 'state'], append=True)[['cases']]
    df_d.columns = ['deaths']

    df = (df.set_index(['country', 'state'], append=True)
            .join(df_r)
            .join(df_d)
            .reset_index(['country', 'state'])
    )
    
    if filter_n_days_100 is not None:
        # Select countries for which we have at least some information
        countries = pd.Series(df.loc[df.days_since_100 >= filter_n_days_100].country.unique())
        df = df.loc[lambda x: x.country.isin(countries)]

    return df