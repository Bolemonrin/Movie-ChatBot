"""Extractive text summarization for TMDB plot overviews.

Pure text processing with no TMDB or LLM knowledge -- the tools call this to
shorten an overview before handing it to the model.
"""
from typing import Optional

import nltk
from sumy.nlp.stemmers import Stemmer
from sumy.nlp.tokenizers import Tokenizer
from sumy.parsers.plaintext import PlaintextParser
from sumy.summarizers.luhn import LuhnSummarizer
from sumy.utils import get_stop_words

# sumy's tokenizer needs this NLTK model; downloading is a no-op once cached.
nltk.download('punkt_tab')

SENTENCE_COUNT = 4


def summarize_overview(overview: Optional[str]) -> Optional[str]:
    '''
    Summarize text using the Luhn algorithm.
    Args:
        overview (str): The input text to summarize.
    Returns:         str: The summary sentences joined into one string.
    '''
    text = overview

    # parse text
    parser = PlaintextParser.from_string(text, Tokenizer('english'))

    # init summarizer
    summarizer = LuhnSummarizer(Stemmer('english'))
    summarizer.stop_words = get_stop_words('english')

    summary = summarizer(parser.document, SENTENCE_COUNT)
    summary_text = " ".join([str(sentence) for sentence in summary])

    return summary_text
