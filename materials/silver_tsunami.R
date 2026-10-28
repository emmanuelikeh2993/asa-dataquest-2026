install.packages(c("tidyverse","readr","janitor","here"))
getwd()
list.files()
# ASA DATAQUEST 2026
library(tidyverse)
library(janitor)
library(here)
# Import the original dataset
wpp_raw <- read.csv("WPP2024_Demographic_Indicators_Medium.csv")
# Check the dimensions
dim(wpp_raw)
# View the column names
names(wpp_raw)
# Inspect the first six observations
head(wpp_raw)
# Check location classifications
table(wpp_raw$LocTypeName)
unique(wpp_raw$Location[wpp_raw$LocTypeName == "Geographic region"])
# create a region data 
regions <- c("Africa","Asia","Europe","Latin America and the Caribbean","Northern America",
  "Oceania")
wpp_regions <- subset(wpp_raw, LocTypeName == "Geographic region" &Location %in% regions)
# Check the result
unique(wpp_regions$Location)
# Number of observations
nrow(wpp_regions)
# create a country data 
wpp_countries <- subset(wpp_raw,LocTypeName == "Country/Area" & Time >= 1950 &
Time <= 2100)
# Number of countries and areas
length(unique(wpp_countries$LocID))
# Total observations
nrow(wpp_countries)

# Check for duplicate country-year records
sum(duplicated(wpp_countries[, c("LocID", "Time")]))
names(wpp_countries)
# Examine countries and their parent identifiers
head(wpp_countries[, c("LocID", "Location", "ISO3_code", "ParentID")], 15)
# Examine regional identifiers
unique(wpp_regions[, c("LocID", "Location", "ParentID") ])
subset(wpp_countries,Location %in% c("Nigeria","Ghana","Japan","Germany","Brazil","United States of America") & Time == 2020,
  select = c( LocID, Location,ISO3_code,ParentID ))

# Create a geographical reference table
geo_lookup <- unique(wpp_raw[, c("LocID","Location","LocTypeName","ParentID")])
# Extract subregions
subregions <- subset(geo_lookup,LocTypeName == "Subregion",select = c(LocID, Location, ParentID))
# Inspect the result
print(subregions, row.names = FALSE)

# Our six main regions
region_ids <- c( 903, 935, 908, 904, 905, 909)
# Create lookup table
geo_lookup <- unique(wpp_raw[, c("LocID", "Location", "ParentID")])
# Check for duplicate location identifiers
stopifnot(!anyDuplicated(geo_lookup$LocID))
# Function to find a country's main region
find_region <- function(location_id) {current_id <- location_id
  visited <- numeric(0)
  repeat {
    if (current_id %in% region_ids) {
      return(current_id)
    }
    
    if (current_id %in% visited) {
      return(NA_real_)
    }
    
    visited <- c(visited, current_id)
    
    position <- match(
      current_id,
      geo_lookup$LocID
    )
    
    if (is.na(position)) {
      return(NA_real_)
    }
    
    current_id <- geo_lookup$ParentID[position]
    
    if (is.na(current_id)) {
      return(NA_real_)
    }
  }
}
# One observation per country
country_lookup <- unique(
  wpp_countries[, c(
    "LocID",
    "Location",
    "ParentID"
  )]
)

# Identify main geographical region
country_lookup$RegionID <- vapply(
  country_lookup$LocID,
  find_region,
  numeric(1)
)

# Match region names
region_names <- c(
  "Africa",
  "Asia",
  "Europe",
  "Latin America and the Caribbean",
  "Northern America",
  "Oceania"
)

country_lookup$Region <- region_names[
  match(country_lookup$RegionID, region_ids)
]
# Number of countries in each region
table(country_lookup$Region, useNA = "ifany")

# Countries without a region
subset(
  country_lookup,
  is.na(Region)
)

# Check selected countries
subset(
  country_lookup,
  Location %in% c(
    "Nigeria",
    "Ghana",
    "Japan",
    "Germany",
    "Brazil",
    "United States of America"
  )
)
# Add Region to the country-year dataset
wpp_master <- merge(
  wpp_countries,
  country_lookup[, c("LocID", "Region")],
  by = "LocID",
  all.x = TRUE,
  sort = FALSE
)

# Arrange by country and year
wpp_master <- wpp_master[
  order(wpp_master$LocID, wpp_master$Time),
]

# Final checks
nrow(wpp_master)

length(unique(wpp_master$LocID))

sum(is.na(wpp_master$Region))

sum(duplicated(wpp_master[, c("LocID", "Time")]))
# Identify countries and areas without regions
missing_regions <- unique(
  wpp_master[
    is.na(wpp_master$Region),
    c("LocID", "Location", "ParentID")
  ]
)

print(missing_regions, row.names = FALSE)
# Correct the five Northern American locations
wpp_master$Region[
  wpp_master$LocID %in% c(60, 124, 304, 666, 840)
] <- "Northern America"
# Check missing geographical classifications
sum(is.na(wpp_master$Region))

# Confirm total observations
nrow(wpp_master)

# Confirm number of countries and areas
length(unique(wpp_master$LocID))

# Confirm no duplicate country-year observations
sum(duplicated(wpp_master[, c("LocID", "Time")]))
# Extract subregion reference table
subregion_lookup <- unique(
  wpp_raw[
    wpp_raw$LocTypeName == "Subregion",
    c("LocID", "Location")
  ]
)

# Match each country's ParentID to a subregion
wpp_master$Subregion <- subregion_lookup$Location[
  match(
    wpp_master$ParentID,
    subregion_lookup$LocID
  )
]

# Northern America is classified directly
# under its own geographical grouping
wpp_master$Subregion[
  wpp_master$Region == "Northern America"
] <- "Northern America"

# Check missing subregions
sum(is.na(wpp_master$Subregion))

# Identify countries without subregions
unique(wpp_master[is.na(wpp_master$Subregion),
    c("LocID", "Location", "ParentID", "Region")])
# Number of countries in each subregion
table(unique(wpp_master[, c("LocID", "Subregion")])$Subregion,useNA = "ifany")
# Select research variables
master_data <- wpp_master[, c("LocID","Location","ISO3_code","Region",
  "Subregion","Time","LEx","LE65", "MedianAgePop","TFR", "CNMR","TPopulation1July")]
# Rename columns for clarity
names(master_data) <- c("CountryID","Country","ISO3","Region","Subregion","Year",
  "LifeExpectancy","LifeExpectancy65", "MedianAge","FertilityRate","NetMigrationRate",
  "Population")
# Inspect the new dataset
head(master_data)
# Confirm dimensions
dim(master_data)
# Create the complete master dataset
master_data <- wpp_master

# Check dimensions
dim(master_data)

# Check column names
names(master_data)
# Columns to appear first
first_columns <- c(
  "LocID",
  "Location",
  "ISO3_code",
  "Region",
  "Subregion",
  "Time"
)

# All remaining columns
other_columns <- setdiff(
  names(master_data),
  first_columns
)

# Reorder the dataset
master_data <- master_data[
  , c(first_columns, other_columns)
]

# Confirm dimensions
dim(master_data)
# Number of countries and areas
length(unique(master_data$LocID))

# Number of observations
nrow(master_data)

# Number of variables
ncol(master_data)

# Missing geographical classifications
sum(is.na(master_data$Region))
sum(is.na(master_data$Subregion))

# Duplicate country-year records
sum(duplicated(
  master_data[, c("LocID", "Time")]
))
write.csv(
  master_data,
  "WPP2024_Master_Dataset.csv",
  row.names = FALSE
)
master_data <- read.csv("WPP2024_Master_Dataset.csv")
names(master_data)

analysis_data <- master_data %>%
  select(
    LocID, Location, ISO3_code,
    Region, Subregion, Time,
    MedianAgePop, TFR, LEx, LE65,
    CNMR, NetMigrations,
    PopGrowthRate, TPopulation1July,
    LExMale, LExFemale)

dim(analysis_data)
names(analysis_data)

baseline_data <- analysis_data %>% filter(Time == 2000)
# Number of countries
nrow(baseline_data)

# Missing values
colSums(is.na(baseline_data))

# Summary of demographic indicators
summary(baseline_data[, c("MedianAgePop", "TFR","LEx", "LE65", "CNMR")])
cluster_vars <- c( "MedianAgePop","TFR","LEx","LE65", "CNMR")
cor(baseline_data[, cluster_vars],use = "complete.obs")
# Ten lowest migration rates
baseline_data %>% arrange(CNMR) %>% select(Location, Region, CNMR) %>%
head(10)
# Ten highest migration rates
baseline_data %>% arrange(desc(CNMR)) %>% select(Location, Region, CNMR) %>%
head(10)
# Model A: Core demographic indicators
cluster_A <- baseline_data[, c("MedianAgePop","TFR","LEx")]
# Model B: Include migration
cluster_B <- baseline_data[, c("MedianAgePop","TFR","LEx","CNMR")]
# Standardise both datasets
cluster_A_scaled <- scale(cluster_A)
cluster_B_scaled <- scale(cluster_B)
# Verify standardisation
round(colMeans(cluster_A_scaled), 3)
round(apply(cluster_A_scaled, 2, sd), 3)
round(colMeans(cluster_B_scaled), 3)
round(apply(cluster_B_scaled, 2, sd), 3)

set.seed(123)
wss_A <- numeric(10)

for (k in 1:10) {
  km <- kmeans(
    cluster_A_scaled,
    centers = k,
    nstart = 50)
  wss_A[k] <- km$tot.withinss}

plot(
  1:10, wss_A,
  type = "b",
  pch = 19,
  xlab = "Number of Clusters (K)",
  ylab = "Within-Cluster Sum of Squares",
  main = "Elbow Method: Model A")

library(cluster)

set.seed(123)

sil_A <- numeric(9)

for (k in 2:10) {
  
  km <- kmeans(
    cluster_A_scaled,
    centers = k,
    nstart = 50
  )
  
  sil <- silhouette(
    km$cluster,
    dist(cluster_A_scaled)
  )
  
  sil_A[k - 1] <- mean(sil[, 3])}

plot(
  2:10, sil_A,
  type = "b",
  pch = 19,
  xlab = "Number of Clusters (K)",
  ylab = "Average Silhouette Width",
  main = "Silhouette Method: Model A")

# Display numerical results
data.frame(
  K = 2:10,
  Average_Silhouette = round(sil_A, 4))
set.seed(123)

# Fit both clustering solutions
km_A2 <- kmeans(
  cluster_A_scaled,
  centers = 2,
  nstart = 50
)

km_A3 <- kmeans(
  cluster_A_scaled,
  centers = 3,
  nstart = 50)

# Number of countries in each cluster
table(km_A2$cluster)
table(km_A3$cluster)
baseline_data %>%
  mutate(Cluster = km_A2$cluster) %>%
  group_by(Cluster) %>%
  summarise(
    Countries = n(),
    Median_Age = round(mean(MedianAgePop), 2),
    Fertility = round(mean(TFR), 2),
    Life_Expectancy = round(mean(LEx), 2))

baseline_data %>%
  mutate(Cluster = km_A3$cluster) %>%
  group_by(Cluster) %>%
  summarise(
    Countries = n(),
    Median_Age = round(mean(MedianAgePop), 2),
    Fertility = round(mean(TFR), 2),
    Life_Expectancy = round(mean(LEx), 2))
# model B 
library(cluster)

set.seed(123)

wss_B <- numeric(10)
sil_B <- numeric(9)

d_B <- dist(cluster_B_scaled)

for (k in 1:10) {
  
  km <- kmeans(
    cluster_B_scaled,
    centers = k,
    nstart = 50
  )
  
  wss_B[k] <- km$tot.withinss
  
  if (k >= 2) {
    sil <- silhouette(km$cluster, d_B)
    sil_B[k - 1] <- mean(sil[, 3])
  }
}

# Elbow plot
plot(
  1:10, wss_B,
  type = "b",
  pch = 19,
  xlab = "Number of Clusters (K)",
  ylab = "Within-Cluster Sum of Squares",
  main = "Elbow Method: Model B"
)

# Silhouette plot
plot(
  2:10, sil_B,
  type = "b",
  pch = 19,
  xlab = "Number of Clusters (K)",
  ylab = "Average Silhouette Width",
  main = "Silhouette Method: Model B"
)

# Numerical silhouette results
data.frame(
  K = 2:10,
  Average_Silhouette = round(sil_B, 4)
)
# Create a transformed migration variable
baseline_data <- baseline_data %>%
  mutate(CNMR_IHS = asinh(CNMR))

# Compare original and transformed migration
summary(baseline_data$CNMR)

summary(baseline_data$CNMR_IHS)
# Create Model C
cluster_C <- baseline_data[, c(
  "MedianAgePop",
  "TFR",
  "LEx",
  "CNMR_IHS"
)]

# Standardise the variables
cluster_C_scaled <- scale(cluster_C)

# Verify standardisation
round(colMeans(cluster_C_scaled), 3)

round(apply(cluster_C_scaled, 2, sd), 3)
library(cluster)

set.seed(123)

sil_C <- numeric(9)

d_C <- dist(cluster_C_scaled)

for (k in 2:10) {
  
  km <- kmeans(
    cluster_C_scaled,
    centers = k,
    nstart = 50
  )
  
  sil <- silhouette(km$cluster, d_C)
  
  sil_C[k - 1] <- mean(sil[, 3])
}

# Compare all three models
comparison <- data.frame(
  K = 2:10,
  Model_A = round(sil_A, 4),
  Model_B = round(sil_B, 4),
  Model_C = round(sil_C, 4)
)

print(comparison)
# Attach the Model A cluster assignments
baseline_clusters <- baseline_data %>%
  mutate(Cluster = km_A3$cluster)

# Number of countries by region and cluster
regional_clusters <- baseline_clusters %>%
  count(Region, Cluster) %>%
  tidyr::pivot_wider(
    names_from = Cluster,
    values_from = n,
    names_prefix = "Cluster_",
    values_fill = 0
  )

print(regional_clusters)
# Repeat K-Means using different random seeds
seeds <- 1:100

cluster_results <- sapply(seeds, function(s) {
  set.seed(s)
  
  kmeans(
    cluster_A_scaled,
    centers = 3,
    nstart = 50
  )$cluster
})

# Compare cluster memberships using Adjusted Rand Index
install.packages("mclust")
library(mclust)

stability <- sapply(1:100, function(i) {
  adjustedRandIndex(
    km_A3$cluster,
    cluster_results[, i]
  )
})

summary(stability)

library(dplyr)
map_clusters <- baseline_clusters %>%
  select(ISO3_code, Cluster) %>%
  mutate(Cluster = factor( Cluster,levels = c(1, 2, 3),labels = c(
  "Youthful", "Intermediate","Older")))
head(map_clusters)
table(map_clusters$Cluster)

install.packages("sf")
install.packages("rnaturalearth")
library(sf)
library(rnaturalearth)
library(dplyr)

# Load world map boundaries
world <- ne_countries(scale = 110,returnclass = "sf")

# Match each country to its cluster
world_clusters <- world %>%
  left_join(map_clusters,by = c("adm0_a3" = "ISO3_code") )

# Check matching results
table(world_clusters$Cluster, useNA = "ifany")
unmatched_countries <- baseline_clusters %>%
  anti_join(world,by = c("ISO3_code" = "adm0_a3")) %>% select(Location, ISO3_code, Cluster)
print(unmatched_countries, n = Inf)
nrow(unmatched_countries)
View(unmatched_countries)
# Load a more detailed world map
world_50 <- ne_countries(scale = 50,returnclass = "sf")
# Match our clusters again
world_clusters_50 <- world_50 %>% left_join(map_clusters,by = c("adm0_a3" = "ISO3_code"))
# Check the new matching results
table(world_clusters_50$Cluster, useNA = "ifany")
remaining_unmatched <- baseline_clusters %>% anti_join( world_50, by = c("ISO3_code" = "adm0_a3")) %>%
select(Location, ISO3_code, Cluster)
print(as_tibble(remaining_unmatched), n = Inf)
world_50 %>% filter( grepl( "South Sudan|Palestine|Kosovo|Western Sahara|French Guiana", name,
ignore.case = TRUE )) %>% st_drop_geometry() %>%
select(name, adm0_a3, iso_a3)
# Create corrected map codes
map_clusters_fixed <- map_clusters %>% mutate(
    MapCode = case_when( ISO3_code == "XKX" ~ "KOS",ISO3_code == "PSE" ~ "PSX",
      TRUE ~ ISO3_code))

# Join corrected codes to the map
world_clusters_fixed <- world_50 %>% left_join(  map_clusters_fixed, by = c("adm0_a3" = "MapCode"))
# Check matching results
table(world_clusters_fixed$Cluster, useNA = "ifany")
library(ggplot2)

ggplot(world_clusters_fixed) +
  geom_sf(aes(fill = Cluster),color = "white",linewidth = 0.15 ) +
  scale_fill_manual(values = c(
      "Youthful" = "#3288bd",
      "Intermediate" = "#e6a23c",
      "Older" = "#279b87" ),
    na.value = "grey85",
    name = "Demographic Cluster",
    labels = c(
      "Cluster 1: Youthful",
      "Cluster 2: Intermediate",
      "Cluster 3: Older" )) +
  coord_sf(expand = FALSE) +
  labs(title = "Global Demographic Clusters in 2000",
    subtitle = "K-Means classification based on median age, fertility and life expectancy",
    caption = "Source: UN World Population Prospects 2024 | Grey: Unmatched geographical units" ) +
  theme_void(base_size = 12) +
  theme(plot.title = element_text(
      size = 17,
      face = "bold",
      hjust = 0.5 ),
plot.subtitle = element_text(size = 10,hjust = 0.5),
    legend.position = "bottom",
    legend.title = element_text(face = "bold"),
    plot.caption = element_text(
      size = 8,
      color = "grey40" ) )

ggplot(world_clusters_fixed) +
  geom_sf(
    aes(fill = Cluster),
    color = "white",
    linewidth = 0.12
  ) +
  scale_fill_manual(
    values = c(
      "Youthful" = "#3288bd",
      "Intermediate" = "#e6a23c",
      "Older" = "#279b87"
    ),
    na.value = "grey85",
    name = NULL,
    labels = c(
      "Youthful",
      "Intermediate",
      "Older"
    ),
    drop = FALSE
  ) +
  coord_sf(
    xlim = c(-180, 180),
    ylim = c(-60, 85),
    expand = FALSE
  ) +
  labs(
    title = "Global Demographic Clusters in 2000",
    subtitle = "Based on median age, fertility and life expectancy",
    caption = "Source: UN World Population Prospects 2024 | Grey: Unmatched areas"
  ) +
  guides(
    fill = guide_legend(
      nrow = 1,
      byrow = TRUE
    )
  ) +
  theme_void(base_size = 12) +
  theme(
    plot.title = element_text(
      size = 17,
      face = "bold",
      hjust = 0.5
    ),
    plot.subtitle = element_text(
      size = 11,
      hjust = 0.5
    ),
    legend.position = "bottom",
    legend.text = element_text(size = 10),
    legend.key.width = grid::unit(0.8, "cm"),
    plot.caption = element_text(
      size = 8,
      hjust = 0.5,
      color = "grey40"
    ),
    plot.margin = margin(15, 15, 15, 15))
ggsave( "Global_Demographic_Clusters_2000.png",
  width = 12,
  height = 6,
  dpi = 300,
  bg = "white")
load("Silver_Tsunami_Workspace.RData")
save.image("Silver_Tsunami_Workspace.RData")
objects_needed <- c("analysis_data", "baseline_clusters")
sapply(objects_needed, exists)

library(dplyr)
# 1. Get each country's original cluster assignment
cluster_lookup <- baseline_clusters %>%
  select(LocID, Cluster)

# 2. Keep historical observations from 2000 to 2023
historical_panel <- analysis_data %>%
  filter(Time >= 2000, Time <= 2023) %>%
  left_join(cluster_lookup, by = "LocID")

dim(historical_panel)

table(historical_panel$Cluster, useNA = "ifany")

range(historical_panel$Time)

sum(is.na(historical_panel$Cluster))
View(historical_panel)
median_age_trend <- historical_panel %>%
group_by(Time, Cluster) %>%
summarise(Mean_Median_Age = mean(MedianAgePop, na.rm = TRUE),
    .groups = "drop")

head(median_age_trend, 9)
tail(median_age_trend, 9)

library(ggplot2)
ggplot(median_age_trend,
  aes(x = Time,
      y = Mean_Median_Age,
      color = factor(Cluster))) +
  geom_line(linewidth = 1.1) +
  geom_point(size = 1.5) +
  scale_color_manual( values = c(
      "1" = "#3288bd",
      "2" = "#e6a23c",
      "3" = "#279b87"),
    labels = c(
      "1" = "Cluster 1: Youthful",
      "2" = "Cluster 2: Intermediate",
      "3" = "Cluster 3: Older")) +
  scale_x_continuous(breaks = seq(2000, 2023, by = 3)) +
  labs(title = "Historical Changes in Median Age by Baseline Cluster",
    subtitle = "Country groups classified using demographic characteristics in 2000",
    x = "Year",
    y = "Mean country-level median age (years)",
    color = "Baseline cluster" ) +
  theme_minimal(base_size = 12) +
  theme( plot.title = element_text(face = "bold"),
    legend.position = "bottom" )
library(dplyr)
library(tidyr)

median_age_change <- median_age_trend %>%
  filter(Time %in% c(2000, 2023)) %>%
  select(Time, Cluster, Mean_Median_Age) %>%
  pivot_wider(names_from = Time,
    values_from = Mean_Median_Age,
    names_prefix = "Year_" ) %>%
  mutate(Absolute_Change = Year_2023 - Year_2000,
    Percentage_Change =
      (Absolute_Change / Year_2000) * 100)
print(median_age_change)
gap_analysis <- median_age_change %>%
  select(Cluster, Year_2000, Year_2023) %>%
  summarise(
    Gap_2_vs_1_2000 = Year_2000[Cluster == 2] - Year_2000[Cluster == 1],
    Gap_2_vs_1_2023 = Year_2023[Cluster == 2] - Year_2023[Cluster == 1],
    Gap_3_vs_2_2000 = Year_2000[Cluster == 3] - Year_2000[Cluster == 2],
    Gap_3_vs_2_2023 = Year_2023[Cluster == 3] - Year_2023[Cluster == 2],
    Gap_3_vs_1_2000 = Year_2000[Cluster == 3] - Year_2000[Cluster == 1],
    Gap_3_vs_1_2023 = Year_2023[Cluster == 3] - Year_2023[Cluster == 1] )

print(gap_analysis)

fertility_trend <- historical_panel %>%
  group_by(Time, Cluster) %>%
  summarise(
    Mean_TFR = mean(TFR, na.rm = TRUE),
    .groups = "drop" )

head(fertility_trend, 9)
library(ggplot2)

ggplot(fertility_trend,
       aes(x = Time, y = Mean_TFR,
           color = factor(Cluster))) +
  geom_line(linewidth = 1) +
  scale_color_manual(
    values = c("1" = "blue",
               "2" = "orange",
               "3" = "darkgreen"),
    labels = c(
      "1" = "Youthful, high-fertility",
      "2" = "Intermediate",
      "3" = "Older, low-fertility" ) ) +
  labs(title = "Fertility Trends Across Baseline Demographic Clusters",
    subtitle = "Unweighted country/area averages, 2000–2023",
    x = "Year",
    y = "Mean Total Fertility Rate (births per woman)",
    color = "Baseline cluster") +
  theme_minimal()

fertility_change <- fertility_trend %>%
  filter(Time %in% c(2000, 2023)) %>%
  select(Time, Cluster, Mean_TFR) %>%
  tidyr::pivot_wider(names_from = Time,
    values_from = Mean_TFR,
    names_prefix = "Year_") %>%
  mutate(
    Absolute_Change = Year_2023 - Year_2000,
    Percentage_Change =
      (Absolute_Change / Year_2000) * 100 )

print(fertility_change)
life_expectancy_trend <- historical_panel %>%
  group_by(Time, Cluster) %>%
  summarise(
    Mean_LEx = mean(LEx, na.rm = TRUE),
    .groups = "drop" )

head(life_expectancy_trend, 9)
library(ggplot2)

#ggplot(life_expectancy_trend,
       aes(x = Time, y = Mean_LEx,
           color = factor(Cluster))) +
  geom_line(linewidth = 1) +
  scale_color_manual(
    values = c(
      "1" = "blue",
      "2" = "orange",
      "3" = "darkgreen"
    ),
    labels = c(
      "1" = "Youthful, high-fertility",
      "2" = "Intermediate",
      "3" = "Older, low-fertility"
    )
  ) +
  labs(
    title = "Life Expectancy Trends Across Baseline Demographic Clusters",
    subtitle = "Unweighted country/area averages, 2000–2023",
    x = "Year",
    y = "Mean Life Expectancy at Birth (years)",
    color = "Baseline cluster" ) +
  theme_minimal()
life_expectancy_change <- life_expectancy_trend %>%
  filter(Time %in% c(2000, 2023)) %>%
  select(Time, Cluster, Mean_LEx) %>%
  tidyr::pivot_wider(
    names_from = Time,
    values_from = Mean_LEx,
    names_prefix = "Year_"
  ) %>%
  mutate(
    Absolute_Change = Year_2023 - Year_2000,
    Percentage_Change =
      (Absolute_Change / Year_2000) * 100
  )

print(life_expectancy_change)

future_panel <- analysis_data %>%
  filter(Time >= 2024, Time <= 2050) %>%
  left_join(cluster_lookup, by = "LocID")

future_median_age <- future_panel %>%
  group_by(Time, Cluster) %>%
  summarise(
    Mean_Median_Age = mean(MedianAgePop, na.rm = TRUE),
    .groups = "drop")

head(future_median_age, 9)
future_median_age_change <- future_median_age %>%
  filter(Time %in% c(2024, 2050)) %>%
  select(Time, Cluster, Mean_Median_Age) %>%
  tidyr::pivot_wider(
    names_from = Time,
    values_from = Mean_Median_Age,
    names_prefix = "Year_"
  ) %>%
  mutate(
    Absolute_Change = Year_2050 - Year_2024,
    Percentage_Change =
      (Absolute_Change / Year_2024) * 100
  )

print(future_median_age_change)
save.image("Silver_Tsunami_Workspace.RData")
