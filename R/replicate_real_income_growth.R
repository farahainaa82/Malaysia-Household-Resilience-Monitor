# Independent replication of the core real-income calculation in base R.
# Python remains the primary workflow for this portfolio.

hies_url <- "https://storage.dosm.gov.my/hies/hies_state.csv"
cpi_url  <- "https://storage.dosm.gov.my/cpi/cpi_2d_state.csv"

hies <- read.csv(hies_url, stringsAsFactors = FALSE)
cpi  <- read.csv(cpi_url, stringsAsFactors = FALSE)

hies$date <- as.Date(hies$date)
cpi$date  <- as.Date(cpi$date)

hies$year <- as.integer(format(hies$date, "%Y"))
cpi$year  <- as.integer(format(cpi$date, "%Y"))

years <- sort(unique(hies$year))
previous_year <- years[length(years) - 1]
latest_year   <- years[length(years)]

hies_2 <- subset(hies, year %in% c(previous_year, latest_year))
cpi_overall <- subset(cpi, division == "overall" &
                           year %in% c(previous_year, latest_year))

annual_cpi <- aggregate(index ~ state + year, data = cpi_overall, FUN = mean)

income_prev <- subset(hies_2, year == previous_year,
                      select = c(state, income_median))
names(income_prev)[2] <- "income_previous"

income_latest <- subset(hies_2, year == latest_year,
                        select = c(state, income_median))
names(income_latest)[2] <- "income_latest"

cpi_prev <- subset(annual_cpi, year == previous_year,
                   select = c(state, index))
names(cpi_prev)[2] <- "cpi_previous"

cpi_latest <- subset(annual_cpi, year == latest_year,
                     select = c(state, index))
names(cpi_latest)[2] <- "cpi_latest"

out <- Reduce(function(x, y) merge(x, y, by = "state"),
              list(income_prev, income_latest, cpi_prev, cpi_latest))

out$nominal_income_growth <- out$income_latest / out$income_previous - 1
out$inflation <- out$cpi_latest / out$cpi_previous - 1
out$real_income_growth <- (1 + out$nominal_income_growth) /
                          (1 + out$inflation) - 1

out <- out[order(out$real_income_growth), ]
print(out)
