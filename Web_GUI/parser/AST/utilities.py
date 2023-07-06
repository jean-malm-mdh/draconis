def swap_in_string(s, s1, s2):
    dummyString = "€€€&&ASDFGHJK"
    return str(s).replace(f"{s1}", dummyString).replace(f'{s2}', f"{s1}").replace(dummyString, f'{s2}')
