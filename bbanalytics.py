import config as cfg

languages = cfg.languages if cfg.languages != [] else None
locations = cfg.locations if cfg.locations != [] else None

def generic_filter(entity, compare_list):
    if not compare_list: return True
    if not entity in compare_list: return False
    return True

def lan_filter(lan):
    return generic_filter(lan, languages)

def loc_filter(loc):
    return generic_filter(loc, locations)
    
if __name__ == "__main__":
    assert(lan_filter("fr") == False)
    assert(loc_filter("usa") == True)
