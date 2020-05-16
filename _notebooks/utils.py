import pandas as pd
import numpy as np
def getComulativeData(name):
    base_url='https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series'
    url = f'{base_url}/time_series_covid19_{name}_global.csv'
    data = pd.read_csv(url, error_bad_lines=False)
    data = data.drop(columns=["Lat", "Long"])
    data = data.melt(id_vars= ["Province/State", "Country/Region"])
    data = pd.DataFrame(data.groupby(['Country/Region', "variable"]).sum())
    data.reset_index(inplace=True) 
    data = data.rename(columns={"Country/Region": "location", "variable": "date", "value": "total_"+name})
    data['date'] =pd.to_datetime(data.date)
    data = data.sort_values(by = "date")
    data.loc[data.location == "US","location"] = "United States"
    data.loc[data.location == "Korea, South","location"] = "South Korea"
    return data

def toPercent(index,child,parent):
    if index==0 :
        return    0
    whole=parent[index-1]
    curr=parent[index]
    if (curr>0):
        if(whole>0):
            # display(whole,curr)
            part=curr-whole
            return (part*100)/whole
    return 0