import torch
print(torch.cuda.is_available())

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
from transformers import pipeline, AutoConfig

# genre_pipe = pipeline("text-classification", model="Ammok/movie-genre-classification")
# genre_pipe = pipeline("text-classification", model="guyyanko/bert-movie-genres-classification")
genre_pipe = pipeline("text-classification", model="PardisSzah/Movie_Genre_Classifier")

TMDB_GENRE_MAPPING = {
    "Action": 28,
    "Action & Adventure": 10759,
    "Adventure": 12,
    "Animation": 16,
    "Comedy": 35,
    "Crime": 80,
    "Documentary": 99,
    "Drama": 18,
    "Family": 10751,
    "Fantasy": 14,
    "History": 36,
    "Horror": 27,
    "Kids": 10762,
    "Music": 10402,
    "Mystery": 9648,
    "News": 10763,
    "Reality": 10764,
    "Romance": 10749,
    "Science Fiction": 878,
    "Sci-Fi & Fantasy": 10765,
    "Soap": 10766,
    "Talk": 10767,
    "TV Movie": 10770,
    "Thriller": 53,
    "War": 10752,
    "War & Politics": 10768,
    "Western": 37    
}

MODEL_TMDB_MAPPING = {
    "LABEL_0": "Action",
    "LABEL_1": "Adventure",
    "LABEL_2": "Animation",
    "LABEL_3": "Comedy",
    "LABEL_4": "Crime",
    "LABEL_5": "Documentary",
    "LABEL_6": "Drama",
    "LABEL_7": "Family",
    "LABEL_8": "Fantasy",
    "LABEL_9": "History"
}

# def genre_classification(input_text: str, top_k: int = 5):
#     # running the model
#     result = genre_pipe(input_text, top_k=top_k)
#     labels = [res['label'] for res in result]
#     scores = [res['score'] for res in result]
    
#     HF_to_TMDB_Map = [TMDB_GENRE_MAPPING.get(lbl, None) for lbl in labels]
    
#     # for i in range(len(HF_to_TMDB_Map)):
#     #     print(HF_to_TMDB_Map[i])
        
#     # for i in range(len(scores)):
#     #     print(scores[i])
    
#     for i in range(len(labels)):
#         print(labels[i])
    

config = AutoConfig.from_pretrained("Ammok/movie-genre-classification")
print(config)  

string = "A movie about love at first sight but ends in heartbreak"
print(genre_pipe(string))