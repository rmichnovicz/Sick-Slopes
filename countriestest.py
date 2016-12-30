import countries

checker = countries.CountryChecker("TM_WORLD_BORDERS-0.3.shx")
print(checker.getCountry(countries.Point(20.0, -100.0)))