import pandas as pd
import plotly.express as px

url = 'https://health-infobase.canada.ca/src/data/covidLive/covid19-epiSummary-voc.csv'  

prov_dict = {
	"AB" : "Alberta",
	"BC" : "British Columbia",
	"CA" : "Canada",
	"MB" : "Manitoba",	
	"NB" : "New Brunswick",
	"NL" : "Newfoundland and Labrador",
	"NS" : "Nova Scotia",
	"NT" : "Northwest Territories",
	"NU" : "Nunavut",
	"ON" : "Ontario",
	"PE" : "Prince Edward Island",
	"QC" : "Quebec",
	"SK" : "Saskatchewan",
	"YK" : "Yukon",
	"YT" : "Yukon"
}

colours = ["#012169", "#E03C31", "green", "lightgray"]

def get_province(prov):
	try:
		return prov_dict[prov]
	except:
		return prov

df = pd.read_csv(url).fillna(0)
df = df[ (df["report_date"] > "2021") & (df["report_date"] < "2023") & (df["b117"] >= 0) & (df["b1351"] >= 0) & (df["p1"] >= 0) ]
df["Province"] = df.apply(lambda r: get_province(r["prov"]), axis=1)

dfuk = df.copy()
dfuk["Variant"] = "B.1.1.7 (UK)"
dfuk["Count"] = dfuk["b117"]

dfsa = df.copy()
dfsa["Variant"] = "B.1.351 (South Africa)"
dfsa["Count"] = dfsa["b1351"]

dfbr = df.copy()
dfbr["Variant"] = "P.1 (Brazil)"
dfbr["Count"] = dfbr["p1"]

dfvoc = dfuk.append(dfsa).append(dfbr)

dfvocmax = dfvoc.groupby(["Province", "Variant"]).max().reset_index() \
[["Province", "Variant", "Count"]] \
.rename(columns={"Count" : "MaxVocCount"}) 

dfvoc = pd.merge(dfvoc, dfvocmax, how="left", left_on=["Province", "Variant"], right_on=["Province", "Variant"])
dfvoc = dfvoc.sort_values(by=["Variant", "MaxVocCount", "Province", "report_date"], ascending=[True, False, True, True])

dfvoc["New"] = dfvoc.groupby(["Province", "Variant"])["Count"].diff()

dfprov = dfvoc[dfvoc["Province"] != "Canada"]

figlineprov = px.line(dfprov, 
       x="report_date", y="Count", color="Variant", facet_col="Province", facet_col_wrap=1,
       labels={"report_date" : "Reported date", "Count" : "Cumulative cases", "Province" : "Province/Territory"},
       title="Cumulative cases with a variant of concern<br>by reported date by province/territory by variant",
       height=5000, template="plotly_white", color_discrete_sequence=colours, facet_row_spacing=0.025
      )

figbarprovd = px.bar(dfprov, x="report_date", y="New", color="Variant", facet_col="Province", facet_col_wrap=1,
       labels={"report_date" : "Reported date", "New" : "New cases", "Province" : "Province/Territory", "Variant" : "Variant of concern"},
       hover_name="Variant",
       title="New cases with a variant of concern by reported date<br>by province/territory",
       height=5000, template="plotly_white", color_discrete_sequence=colours, facet_row_spacing=0.025
       )
       
dfcan = dfvoc[dfvoc["Province"] == "Canada"]

figlinecan_c = px.line(dfcan, 
       x="report_date", y="Count", color="Variant", 
       labels={"report_date" : "Reported date", "Count" : "Cumulative cases"},
       title="Cumulative cases in Canada with a variant of concern<br>by reported date by variant",
       template="plotly_white", color_discrete_sequence=colours
      )
      

figbarcan_d = px.bar(dfcan, x="report_date", y="New", color="Variant",
       labels={"report_date" : "Reported date", "New" : "New cases", "Variant" : "Variant of concern"},
       hover_name="Variant",
       title="New cases in Canada with a variant of concern by reported date",
       template="plotly_white", color_discrete_sequence=colours
       )    

