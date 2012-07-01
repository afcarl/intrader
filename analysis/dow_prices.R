require(ggplot2)
require(reshape)
require(scales)
require(data.table)

dow <- data.table(read.csv('/Users/omnijinx/Documents/repos/intrader/dow_export.csv', header = TRUE))
price <- data.table(read.csv('/Users/omnijinx/Documents/repos/intrader/intrade_export.csv', header = TRUE))

dow$dow <- as.numeric(sub(',', '', dow$dow))
dow <- dow[time >= 1340631000]

# dow.zoom <- dow[time >= 1340721000 & time <= 1340744400]
# alpha
dow.zoom <- dow[time >= 1340725000 & time <= 1340730000]
# beta
dow.zoom <- dow[time >= 1340726000 & time <= 1340726060]
# gamma
dow.zoom <- dow[time >= 1340725000 & time <= 1340726300]
# delta
min_time <- 1340725200
max_time <- 1340725400
dow.zoom <- dow[time >= min_time & time <= max_time]
dow.zoom$dow <- ((dow.zoom$dow - 12514.47) / 12640.78) * 10000

# alpha 
price.zoom <- price[time >= 1340725000000 & time <= 1340730000000 & contract == 'DOW.26JUN.HIGHER']
# beta
price.zoom <- price[time >= 1340726000000 & time <= 1340726060000 & contract == 'DOW.26JUN.HIGHER']
# gamma
price.zoom <- price[time >= 1340725000000 & time <= 1340726300000 & contract == 'DOW.26JUN.HIGHER']
price.zoom <- price[time >= min_time * 1000 & time <= max_time * 1000 & contract == 'DOW.26JUN.HIGHER']


ggplot(dow.zoom, aes(x=time, y=dow)) +
  geom_line() + geom_point() + scale_x_continuous(limits = c(min_time, max_time))

ggplot(price.zoom[bid_ask=='BID'], aes(x=time, y=price)) +
  geom_line() + geom_point() + scale_x_continuous(limits = c(min_time * 1000, max_time * 1000))

price.zoom$time <- price.zoom$time / 1000

p <- ggplot() +
  geom_line(data = dow.zoom, aes(x = time, y = dow)) +
  geom_line(data = price.zoom, aes(x = time, y = price, group = bid_ask, colour = bid_ask))
p