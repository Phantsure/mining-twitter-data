import tweepy
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy.streaming import StreamListener
import json
import operator 
from collections import Counter
from nltk.corpus import stopwords
import string
from nltk import bigrams
from collections import defaultdict
import sys
import vincent

# used for authentication, OAUTH
consumer_key = 'Ro42n9uw4qqUygzjxAWd8C3EU'
consumer_secret = '4Myp4ybUlfRhGFYI2VCwVBOPlxprZ33Q0GxiDLIsqvloNlmLQB'
access_token = '835728408462176257-hElgElHrrQJUucLfEoa8mcaliejMVfJ'
access_secret = 'YXmbzC8r71Tbgp9IFJtnIMtcrooYRVE8wCS18jok5oYD9'
 
auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
 
api = tweepy.API(auth)

import re

# making tokens more useful not just each character
emoticons_str = r"""
    (?:
        [:=;] # Eyes
        [oO\-]? # Nose (optional)
        [D\)\]\(\]/\\OpP] # Mouth
    )"""
 
regex_str = [
    emoticons_str,
    r'<[^>]+>', # HTML tags
    r'(?:@[\w_]+)', # @-mentions
    r"(?:\#+[\w_]+[\w\'_\-]*[\w_]+)", # hash-tags
    r'http[s]?://(?:[a-z]|[0-9]|[$-_@.&amp;+]|[!*\(\),]|(?:%[0-9a-f][0-9a-f]))+', # URLs
 
    r'(?:(?:\d+,?)+(?:\.?\d+)?)', # numbers
    r"(?:[a-z][a-z'\-_]+[a-z])", # words with - and '
    r'(?:[\w_]+)', # other words
    r'(?:\S)' # anything else
]
    
tokens_re = re.compile(r'('+'|'.join(regex_str)+')', re.VERBOSE | re.IGNORECASE)
emoticon_re = re.compile(r'^'+emoticons_str+'$', re.VERBOSE | re.IGNORECASE)

# processing and collecting tokens  
def tokenize(s):
    return tokens_re.findall(s)
 
def preprocess(s, lowercase=False):
    tokens = tokenize(s)
    if lowercase:
        tokens = [token if emoticon_re.search(token) else token.lower() for token in tokens]
    return tokens

# nltk.download('stopwords')

punctuation = list(string.punctuation)
# Making list of some useless words, punctuations and emoticons which hinders aur analysis. e.g. to, if, as, ... 
stop = stopwords.words('english') + punctuation + ['RT', 'via', u'\u2026', u'\u261e'] # some emoticons included

com = defaultdict(lambda : defaultdict(int))

# Taking search word
# search_word = sys.argv[1]
search_word = "python"

fname = 'python.json'
# Json data set opening
with open(fname, 'r') as f:
    count_all = Counter()
    count_search = Counter()
    for line in f:
        # Loads as dictionary
        tweet = json.loads(line)
        # Create a list with all the terms
        terms_all = [term for term in preprocess(tweet['text']) if term not in stop]
        # 2 words in context more relatable to analysis
        terms_bigram = bigrams(terms_all)
        # Count terms only once, equivalent to Document Frequency
        terms_single = set(terms_all)
        # Count hashtags only
        terms_hash = [term for term in preprocess(tweet['text']) 
                    if term.startswith('#')]
        # Count terms only (no hashtags, no mentions)
        terms_only = [term for term in preprocess(tweet['text']) 
                    if term not in stop and
                    not term.startswith(('#', '@'))] 
                    # mind the ((double brackets))
                    # startswith() takes a tuple (not a list) if 
                    # we pass a list of inputs
        # Update the counter as per name suggests
        count_all.update(terms_only)

        # Updates the counter if search_word in terms_only
        if search_word in terms_only:
            count_search.update(terms_only)
    
        # Build co-occurence matrix
        for i in range(len(terms_only) - 1):
            for j in range(i+1, len(terms_only)):
                w1, w2 = sorted([terms_only[i], terms_only[j]])
                if w1 != w2:
                    com[w1][w2] += 1

    # Prints the result for co-occurences for search_word
    print("Co-occurences for %s" %search_word)
    print(count_search.most_common(10))

    com_max = []
    # For each term, look for most common co-occurent terms
    for t1 in com:
        t1_max_terms = sorted(com[t1].items(), key=operator.itemgetter(1))
        for t2, t2_count in t1_max_terms:
            com_max.append(((t1, t2), t2_count))
    # Get the most frequent co-occurences
    term_max = sorted(com_max, key=operator.itemgetter(1), reverse=True)
    """print(term_max[:5])"""

    # Print the first 5 most frequent words
    """print(count_all.most_common(10))"""

    word_freq = count_all.most_common(10)
    labels, freq = zip(*word_freq)
    data = {'data':freq, 'x':labels}
    bar = vincent.Bar(data, iter_idx='x')
    bar.to_json('term_freq.json')
