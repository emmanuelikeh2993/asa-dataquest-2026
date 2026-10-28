head(master_data)
View(master_data)
names(master_data)
library(dplyr)
tsunami_data <- master_data %>% select(Location, ISO3_code, Region, Subregion, Time,TPopulation1July,                             
MedianAgePop,TFR, MAC, LEx, LE65, LE80, Q1560, IMR,CNMR, NetMigrations,CBR, CDR, NatChangeRT,PopGrowthRate)           
 # data inspection    
head(tsunami_data)
dim(tsunami_data)                     
n_distinct(tsunami_data$Location)     
sum(is.na(tsunami_data))              
range(tsunami_data$Time)        
glimpse(tsunami_data)   
# extract out the base year 
base_year <- tsunami_data %>% filter(Time == 2000)
#standardize the series
standard <- scale(base_year$MedianAgePop)
# k-means cluster  
set.seed(42)
km <- kmeans(standard, centers = 3, nstart = 25)
base_year$cluster <- km$cluster
km$size
km$centers
names(base_year)
split(base_year$Location, km$cluster)
# Relabel cluster by rank of median age (1,2,3 are arbitrary)
ord <- base_year %>% group_by(cluster) %>% 
                     summarise(m = mean(MedianAgePop)) %>% 
                     arrange(m)
base_year$group <- factor(base_year$cluster, levels = ord$cluster,
                          labels = c("Young","Middle","Old"))
# iso3 code from country name
#install.packages("countrycode")
library(countrycode)
library(sf)
library(rnaturalearth)
base_year$ISO3_code <- countrycode(base_year$Location,"country.name", "iso3c")
# map data 
world <- ne_countries(scale = "medium", returnclass = "sf")
map_df <- world %>% left_join(base_year %>% select(ISO3_code, group), by = c("adm0_a3" = "ISO3_code"))
# plot
ggplot(map_df) + 
  geom_sf(aes(fill = group), colour = "white", linewidth = 0.1) +
  scale_fill_manual(values = c(Young = "#d73027", Middle = "#fee090", Old ="#4575b4"),
                    na.value = "grey85", name = "median age cluster") +
  theme_minimal() +
  labs(title = "cluster of countries")
ggsave("cluster_map.png", width = 10,height = 5,dpi = 300)
save.image("Silveunami_Workspace.RData")
