import re


class FindSpam:
  rules = [
   {'regex': "(?i)\\b(baba(ji)?|nike|[Vv]ashikaran|[Ss]umer|[Kk]olcak|porn|[Mm]olvi|[Jj]udi [Bb]ola|ituBola.com|[Ll]ost [Ll]over|11s)\\b", 'all': True,
    'sites': [], 'reason': "Bad keyword detected"},
   {'regex': "\\+\\d{10}|\\+?\\d{2}[\\s\\-]?\\d{8,1o}", 'all': True,
    'sites': ["patents.stackexchange.com"], 'reason': "Phone number detected"},
   {'regex': "(?i)\\b([Nn]igga|[Nn]igger|niga|[Aa]sshole|crap|fag|[Ff]uck(ing?)?|idiot|[Ss]hit|[Ww]hore)s?\\b", 'all': True,
    'sites': [], 'reason': "Offensive title detected",'insensitive':True},
   {'regex': "^(?=.*[A-Z])[^a-z]*$", 'all': True, 'sites': [], 'reason': "All-caps title"}
  ]

  @staticmethod
  def testpost(title, site):
    result = [];
    for rule in FindSpam.rules:
      if rule['all'] != (site in rule['sites']):
        if re.compile(rule['regex']).search(title):
          result.append(rule['reason'])
    return result
