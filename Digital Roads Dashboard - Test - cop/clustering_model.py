from connectdb import connect
import pandas as pd 
import geopandas as gpd
import numpy as np
from shapely import wkb
import warnings
warnings.filterwarnings('ignore')


from sklearn.impute import KNNImputer
from sklearn.preprocessing import StandardScaler
from sklearn import preprocessing
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn_extra.cluster import KMedoids
from kneed import KneeLocator # sert à détecter l'hyper-parametre K pour la méthode KMeans
from sklearn.cluster import AgglomerativeClustering

from sklearn.metrics import silhouette_score




def train_clustring_modal(cites_base_df, df, model, k):
    classes = []
    if model == 'cah':
        classes = AgglomerativeClustering(n_clusters = k).fit(df).labels_
    elif model == 'kmeans':
        classes = KMeans(k).fit(df).labels_
    else:
        classes = KMedoids(k).fit(df).labels_

    
    cites = pd.DataFrame(
        {
        'classe': classes,
        'city_population' : cites_base_df["city_population"],
        'city_name': cites_base_df["city_name_x"],
        'city_geom': cites_base_df["city_geom"]
        }
    )

    my_geo_df = gpd.GeoDataFrame(cites, geometry='city_geom', crs="epsg:3857")
    my_geo_df = my_geo_df.to_crs(epsg=4326)

    fig = my_geo_df.explore(
        column="classe", # make choropleth based on "BoroName" column
        tooltip=["city_name","city_population", "classe"], # show "BoroName" value in tooltip (on hover)
        popup=True, # show all values in popup (on click)
        tiles="CartoDB positron", # use "CartoDB positron" tiles
        cmap="Set1", # use "Set1" matplotlib colormap
        style_kwds=dict(color="black") # use black outline
    )

    return my_geo_df, fig


def data_processing(features, type_clustering):
    print("Start clustering .... ")
    lines_in_cites, line_length_in_cites, tags_in_cites = connect(type_clustering)

    def transform_tag(a):
        d={}
        key = ''
        for i in a.replace('"','').split(','):
            key = i.lstrip().split("=>")[0]
            if key == 'lanes' or key == 'maxspeed':
                d[key] =  int(i.split("=>")[1].split(" ")[0])

        return d

    lines_in_cites.line_tags = lines_in_cites.line_tags.apply(transform_tag)

    lines_in_cites = lines_in_cites.join(pd.json_normalize(lines_in_cites.line_tags))
    lines_in_cites.drop(["line_tags", "line_osm_id"], axis=1, inplace = True)

    lines_in_cites.drop(lines_in_cites[(lines_in_cites.line_type == "path") | (lines_in_cites.line_type == "pedestrian") | (lines_in_cites.line_type == "step") | (lines_in_cites.line_type == "steps") | (lines_in_cites.line_type == "track") | (lines_in_cites.line_type == "unclassified") | (lines_in_cites.line_type == "road") | (lines_in_cites.line_type == "rest_area") | (lines_in_cites.line_type == "corridor") | (lines_in_cites.line_type == "bus_guideway") | (lines_in_cites.line_type == "platform") | (lines_in_cites.line_type == "pedestrian") | (lines_in_cites.line_type == "crossing") | (lines_in_cites.line_type == "bridleway") | (lines_in_cites.line_type == "proposed") | (lines_in_cites.line_type == "construction") |  (lines_in_cites.line_type == "escape") | (lines_in_cites.line_type == "raceway") |  (lines_in_cites.line_type == "cycleway") | (lines_in_cites.line_type == "service") | (lines_in_cites.line_type == "services") ].index, inplace=True)

    lines_in_cites_groupedby_speed_lanes = lines_in_cites.groupby(["city_osm_id","city_name","line_type"])[["maxspeed","lanes"]].median().reset_index()

    # mode = lambda x: x.mode() if len(x) > 2 else np.array(x)[0]
    lines_in_cites_groupedby_surface = lines_in_cites.groupby(["city_osm_id","line_type"])["line_surface"].agg(lambda x: x.mode(dropna=False).iloc[0]).to_frame().reset_index()

    type_speed_with_surface = lines_in_cites_groupedby_speed_lanes.merge(lines_in_cites_groupedby_surface, on=["city_osm_id", "line_type"], how = 'inner')
    lines_df = type_speed_with_surface.merge(line_length_in_cites, right_on=["city_osm_id", "highway"], left_on=["city_osm_id", "line_type"], how='inner')
    lines_df.drop(["id", "city_name_y" , "highway"], axis=1, inplace=True)

    lines_df["maxspeed"].loc[(lines_df.line_type == 'footway') |(lines_df.line_type == 'living_street' ) ] = 20
    lines_df["lanes"].loc[(lines_df.line_type == 'footway') | (lines_df.line_type == 'living_street' ) ] = 1


    for col in lines_df[["maxspeed", "lanes"]]:
        imputer = KNNImputer(missing_values = np.nan, n_neighbors = 5)
        lines_df[col] = [round(i[0]) for i in imputer.fit_transform(lines_df[col].values.reshape(-1, 1))]

    lines_df.line_surface = lines_df.line_surface.astype('str')
    lines_df["line_surface"].loc[(lines_df.line_surface == '[]') | (lines_df.line_surface == 'None')] = "undefined"


    lines_df["line_surface"].loc[(lines_df.line_surface == "['asphalt' 'paved']") | (lines_df.line_surface == "['asphalt' 'unpaved']") | (lines_df.line_surface == "['asphalt' 'paved' 'unpaved']") ] = "mixed"

    lines_df = lines_df.set_index(["city_osm_id", "city_name_x", "line_type"]).unstack(2)

    lines_df = lines_df.set_axis(lines_df.columns.map('_'.join), axis = 1, inplace = False).reset_index()

    nan_not_accepted = list(lines_df.drop(["city_osm_id","city_name_x"], axis=1).columns)
    nan_not_accepted_in_non_category = [i for i in nan_not_accepted if i[:12] != "line_surface"]
    nan_not_accepted_in_category = [i for i in nan_not_accepted if i[:12] == "line_surface"]

    for column in nan_not_accepted_in_non_category:
        lines_df[column] = lines_df[column].replace(np.NaN, 0)

    for column in nan_not_accepted_in_category:
        lines_df[column] = lines_df[column].replace(np.NaN, "inexistent")


    def convert(row_geo):
        return wkb.loads(row_geo, hex= True)

    tags_in_cites.city_geom = tags_in_cites.city_geom.apply(convert)
    features.extend(["city_osm_id","city_population", "city_geom"])
    tags_in_cites.drop(tags_in_cites.columns.difference(features), 1, inplace=True)

    lines_df = lines_df.merge(tags_in_cites, right_on="city_osm_id", left_on="city_osm_id", how='inner')

    cites_df = lines_df.copy()
    print(cites_df)

    cites_df_final = cites_df.drop(["city_osm_id","city_name_x", "city_population", "city_geom"], axis=1)

    nrows = cites_df_final.shape[0]
    for col in cites_df_final.columns:
        if(nrows - cites_df_final[col].count()) / nrows > 0.6:
            print(f'La colonne {col} a été supprimé.')
            cites_df_final.drop(col, axis = 1, inplace = True)

    nan_not_accepted_in_non_category = [i for i in list(cites_df_final.columns) if i[:12] == "line_surface"]

    for col in cites_df_final.drop(nan_not_accepted_in_non_category, axis=1):
        imputer = KNNImputer(missing_values = np.nan, n_neighbors = 3)
        cites_df_final[col] = [round(i[0]) for i in imputer.fit_transform(cites_df_final[col].values.reshape(-1, 1))]


    le = preprocessing.LabelEncoder()
    for col in nan_not_accepted_in_non_category:
        cites_df_final[col] = le.fit_transform(cites_df_final[col])

    for col in cites_df_final.columns:
        q25, q75 = np.percentile(cites_df_final[col].dropna(), 25), np.percentile(cites_df_final[col].dropna(), 75)
        iqr = q75 - q25
        upper_limit = q75 + 1.5 * iqr
        lower_limit = q25 - 1.5 * iqr
        cites_df_final[col] = np.where(
            cites_df_final[col] < lower_limit,
            lower_limit,
            np.where(
                cites_df_final[col] > upper_limit,
                upper_limit,
                cites_df_final[col]
            )
        )

    df_scaled = StandardScaler().fit_transform(cites_df_final) 


    # Pca 
    df_pca = PCA(svd_solver='randomized', random_state=42).fit(df_scaled)
    cumsum_variance = np.cumsum(df_pca.explained_variance_ratio_)

    nb_components = 0
    for i in cumsum_variance:
        if i < 0.9:
            nb_components +=1

    df_pca = PCA(n_components=nb_components).fit_transform(cites_df_final)

    nb_clusters = range(2, int(df_pca.shape[0]/2+2))
    inertie = []
    models = []
    for K in nb_clusters:
        kmeans = KMeans(K)
        kmeans.fit(df_pca)
        models.append(kmeans)
        inertie.append(kmeans.inertia_)

    kl = KneeLocator(nb_clusters, inertie, S=1.0, curve='convex', direction='decreasing')
    K = kl.elbow

    kmeans = models[K]
    classes_kmeans = kmeans.labels_

    cah = AgglomerativeClustering(n_clusters = 6).fit(df_pca)
    classes_cah = cah.labels_

    nb_clusters_kmedoids = range(2, int(df_pca.shape[0]/2+2))
    inertie_kmedoids = []
    models_kmedoids = []
    for K in nb_clusters_kmedoids:
        kmedoids = KMedoids(K)
        kmedoids.fit(df_pca)
        models_kmedoids.append(kmedoids)
        inertie_kmedoids.append(kmedoids.inertia_)

    kl_KMedoids = KneeLocator(nb_clusters_kmedoids, inertie_kmedoids, S=1.0, curve='convex', direction='decreasing')
    K_KMedoids = kl_KMedoids.elbow
    kmedoids = models_kmedoids[K_KMedoids]
    classes_kmedoids = kmedoids.labels_

    silhouette_cah = silhouette_score(df_pca, classes_cah)
    silhouette_kmeans = silhouette_score(df_pca, kmeans.labels_)
    silhouette_kmedoids = silhouette_score(df_pca, kmedoids.labels_)


    models_dict = {"cah":silhouette_cah, "kmeans":silhouette_kmeans, "kmedoids":silhouette_kmedoids}
    bestmodel = max(models_dict, key=models_dict.get )

    
    print(bestmodel)
    finale_k = 0
    if bestmodel == 'cah':
        finale_k = 6
    elif bestmodel == 'kmeans':
        finale_k = K
    else:
        finale_k = K_KMedoids

    print(finale_k)
    df, fig = train_clustring_modal(cites_df, df_pca, bestmodel, finale_k)
    return cites_df, df_pca, bestmodel, finale_k, df, fig



# cities_base_final, df_final, best_model, current_k, geo_df, fig = data_processing(["traffic_calming", "traffic_calming"], "cites")

# print(type(fig))
