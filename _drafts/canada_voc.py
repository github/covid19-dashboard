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

def get_area(prov):
	if prov == 'YK':
		return 'YT'
	else:
		return prov


df = pd.read_csv(url).fillna(0)
dfclean = df[ (df["report_date"] > "2021") & (df["report_date"] < "2023") & (df["b117"] >= 0) & (df["b1351"] >= 0) & (df["p1"] >= 0) ]
dfclean["Province"] = dfclean.apply(lambda r: get_province(r["prov"]), axis=1)
dfclean["Area"] = dfclean.apply(lambda r: get_area(r["prov"]), axis=1)

dfAlpha = dfclean.copy()
dfAlpha["Variant"] = "B.1.1.7 (Alpha)"
dfAlpha["Count"] = dfAlpha["b117"]

dfBeta = dfclean.copy()
dfBeta["Variant"] = "B.1.351 (Beta)"
dfBeta["Count"] = dfBeta["b1351"]

dfGamma = dfclean.copy()
dfGamma["Variant"] = "P.1 (Gamma)"
dfGamma["Count"] = dfGamma["p1"]

dfvoc = dfAlpha.append(dfBeta).append(dfGamma)

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

# Accessibility

date_name = "Date"         


def join(df, area, variant):
	dfarea = dfclean[dfclean["Area"] == area][["report_date", variant]].rename(columns={"report_date" : date_name, variant : area}) 
	return pd.merge(df, dfarea, how="left", left_on=[date_name], right_on=[date_name])

def create_table(variant):
	date_max = dfclean.max()["report_date"]
	df_max = dfclean[(dfclean["Area"]!="CA") & (dfclean["report_date"] == date_max)][["Area", variant]].sort_values(by=[variant, "Area"], ascending=[False, True])
	areas = df_max["Area"].tolist()

	df_variant = pd.DataFrame()
	df_variant[date_name] = dfclean[dfclean["Area"]=="CA"]["report_date"]

	for area in areas:
	    df_variant = join(df_variant, area, variant)
	    
	df_variant = join(df_variant, "CA", variant)
	return df_variant.set_index(date_name).sort_values(by=[date_name], ascending=[False]).round().astype(int)
	
df_Alpha = create_table("b117")
df_Beta = create_table("b1351")
df_Gamma = create_table("p1")

