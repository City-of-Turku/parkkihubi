from faker import Factory as FakerFactory

fake = FakerFactory.create('fi_FI')
fake.seed(777)

fake.postcode('20100')
