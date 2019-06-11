delegates = Variable()

@construct
def seed():
    masternodes.set([
        "8143f569f258c33de00d71a6527eadd5e22a88b0f16bee3f13230d26dd8a5e46",
        "64cdc0774705e09d1f2c3288766721ad1fa4a9cfd2be8260c127c0ea3475dd8e",
        "5568d257e567c043e7fbf8d6425256a174da2719f6829bbe46a4c2bbfc8bb9a4",
        "93aeefec5d87bc890b02fec280ab9c79803d2ab71d1cb274d7090e9b84cd6f8a"
    ])


@export
def get_all():
    return delegates.get()