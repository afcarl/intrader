require(rmongodb)
require(ggplot2)
require(scales)
require(reshape)
require(data.table)

mongo <- mongo.create()
if (!mongo.is.connected(mongo))
  error("No connection to MongoDB")

db <- 'intrade'
db.closing <- paste(db, 'closing', sep='.')

c_contract <- c()
c_date <- c()
c_price <- c()
c_low <- c()
c_high <- c()

cursor <- mongo.find(mongo, db.closing)
while (mongo.cursor.next(cursor)){
  rec <- mongo.cursor.value(cursor)
  # ensure that all fields exist before appending to vectors
  continuer <- FALSE
  for (val in c('contract_id', '@dt', '@price', '@sessionLo', '@sessionHi')){
    if (is.null(mongo.bson.value(rec, val))){
      continuer <- TRUE
    }
  }
  if (!continuer){
    c_contract <- append(c_contract, mongo.bson.value(rec, 'contract_id'))
    c_date <- append(c_date, mongo.bson.value(rec, '@dt'))
    c_price <- append(c_price, mongo.bson.value(rec, '@price'))
    c_low <- append(c_low, mongo.bson.value(rec, '@sessionLo'))
    c_high <- append(c_high, mongo.bson.value(rec, '@sessionHi'))
  }
}

closing <- data.table(cbind(c_contract, c_date, c_price, c_low, c_high))
closing$c_date <- as.numeric(as.character(closing$c_date))
closing$c_price <- as.numeric(as.character(closing$c_price))
closing$c_low <- as.numeric(as.character(closing$c_low))
closing$c_high <- as.numeric(as.character(closing$c_high))
closing.short <- closing[c_date >= 1338508800000]
closing.combined <- closing.short[, list(sum(c_price), sum(c_low), sum(c_high)), by=factor(c_date)]
setnames(closing.combined, names(closing.combined), c('c_date', 'c_price', 'c_low', 'c_high'))