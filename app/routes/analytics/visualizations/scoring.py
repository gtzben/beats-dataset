"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-02-07
"""


# TIPI scoring function
def score_tipi(df_grouped):
    """
    Compute TIPI scores for participant. 
    Five Personality Traits:

    Extraversion (EXT): 1 and 6R
    Agreeableness (AGR): 2R and 7
    Conscientiousness (CON): 3 and 8R
    Emotional Stability (ES): 4R and 9
    Openness (OPN): 5 and 10R

    Reverse score: recode a 7 with a 1, a 6 with a 2, a 5 with a 3, etc.)
    """

    # Define scoring logic
    tipi_scores = {
        ("TIPI", "EXT"): lambda df: (df.loc[df["item"] == 1, "response"].values[0] +
                           (8 - df.loc[df["item"] == 6, "response"].values[0])) / 2,
        ("TIPI", "AGR"): lambda df: (df.loc[df["item"] == 7, "response"].values[0] +
                           (8 - df.loc[df["item"] == 2, "response"].values[0])) / 2,
        ("TIPI", "CON"): lambda df: (df.loc[df["item"] == 3, "response"].values[0] +
                           (8 - df.loc[df["item"] == 8, "response"].values[0])) / 2,
        ("TIPI","ES"): lambda df: (df.loc[df["item"] == 9, "response"].values[0] +
                           (8 - df.loc[df["item"] == 4, "response"].values[0])) / 2,
        ("TIPI","OPN"): lambda df: (df.loc[df["item"] == 5, "response"].values[0] +
                           (8 - df.loc[df["item"] == 10, "response"].values[0])) / 2,
    }

    # Make sure responses are int
    df_grouped["response"] = df_grouped["response"].astype(int)

    # Calculate scores
    scores = {dimension: score_func(df_grouped) for dimension, score_func in tipi_scores.items()}
    return scores


def score_panas(df_grouped):
    """
    Compute PANAS scores.
    Postive Affect Score (PAS): 1, 3, 5, 9, 10, 12, 14, 16, 17, 19
    Negative Affect Score (NAS): 2, 4, 6, 7, 8, 11, 13, 15, 18, 20

    """

    panas_scores = {
        ("PANAS","PAS"): lambda df: df.loc[df["item"].isin([1, 3, 5, 9, 10, 12, 14, 16, 17, 19])]["response"].sum(),
        ("PANAS", "NAS"): lambda df: df.loc[df["item"].isin([2, 4, 6, 7, 8, 11, 13, 15, 18, 20])]["response"].sum()
    }

    # Make sure responses are int
    df_grouped["response"] = df_grouped["response"].astype(int)

    #Calculate scores
    scores = {dimension: score_func(df_grouped) for dimension, score_func in panas_scores.items()}

    return scores

def score_pss(df_grouped):
    """
    Compute PSS score.
    Reversed items: 4,5,6,7,9,10,13
    
    Reverse score: recode a 4 with a 0, a 3 with a 1, a 2 stays 2, 1 with a 3 and 4 with a 0)
    """

    pss_score = {
        ("PSS",""): lambda df: ((df.loc[df["item"].isin([1,2,3,8,11,12,14])]["response"].sum())+
                                ((5-df.loc[df["item"].isin([4,5,6,7,9,10,13])]["response"]).sum()))
    }

    # Make sure responses are int
    df_grouped["response"] = df_grouped["response"].astype(int)

    #Calculate scores
    score = {dimension: score_func(df_grouped) for dimension, score_func in pss_score.items()}

    return score


def score_phq9(df_grouped):
    """
    Compute PHQ9 score.
    
    """

    phq9_score = {
        ("PHQ9",""): lambda df: df["response"].sum()}

    # Make sure responses are int
    df_grouped["response"] = df_grouped["response"].astype(int)

    #Calculate scores
    score = {dimension: score_func(df_grouped) for dimension, score_func in phq9_score.items()}

    return score


def score_stompr(df_grouped):
    """
    Compute STOMP-R scores.
    Four broad music-preference dimensions:

    Reflective & Complex (RC): 2, 3, 4, 7, 11, 12, 13, 15
    Intense & Rebellious (IR): 1, 10, 17, 21
    Upbeat & Conventional (UC): 5, 9, 14, 16, 20, 23
    Energetic & Rhythmic (ER): 6, 8, 18, 19, 22

    """

    stompr_scores = {
        ("STOMPR","RC"): lambda df: df.loc[df["item"].isin([2, 3, 4, 7, 11, 12, 13, 15])]["response"].mean().round(2),
        ("STOMPR", "IR"): lambda df: df.loc[df["item"].isin([1, 10, 17, 21])]["response"].mean().round(2),
        ("STOMPR", "UC"): lambda df: df.loc[df["item"].isin([5, 9, 14, 16, 20, 23])]["response"].mean().round(2),
        ("STOMPR", "ER"): lambda df: df.loc[df["item"].isin([6, 8, 18, 19, 22])]["response"].mean().round(2)
    }

    # Make sure responses are int
    df_grouped["response"] = df_grouped["response"].astype(int)

    #Calculate scores
    scores = {dimension: score_func(df_grouped) for dimension, score_func in stompr_scores.items()}

    return scores


def score_gms(df_grouped):
    """
    Compute Goldsmiths scores.
    Five independent dimensions and one overal score:

    Active Engagement (AE): 1, 3, 8, 15, 21, 24, 28, 34, 38
    Perceptual Abilities (PA): 5, 6, 11, 12, 13, 18, 22, 23, 26
    Musical Training (MT): 14, 27, 32, 33, 35, 36, 37
    Singing Abilities (SA): 4, 7, 10, 17, 25, 29, 30
    Emotions (EMO): 2, 9, 16, 19, 20, 31

    General Sophistication (GS): 1, 3, 4, 7, 10, 12, 14, 15, 17, 19, 23, 24, 25, 27, 29, 32, 33, 37

    Categorial Items: 32, 33, 34, 35, 36 37, 38 
    Reverse-scored items: 9, 11, 13, 14, 17, 21, 23, 25, 27
    """

    gsm_cat = {32: ["0", "1", "2", "3", "4-5", "6-9", "10 or more"],
               33: ["0", "0.5", "1", "1.5", "2", "3-4", "5 or more"],
               34: ["0", "1", "2", "3", "4-6", "7-10", "11 or more"],
               35: ["0", "0.5", "1", "2", "3", "4-6", "7 or more"],
               36: ["0", "0.5", "1", "2", "3-5", "6-9", "10 or more"],
               37: ["0", "1", "2", "3", "4", "5", "6 or more"],
               38: ["0-15 min", "15-30 min", "30-60 min", "60-90 min", "2 hrs", "2-3 hrs", "4 hrs or more"]} 

    gms_scores = {
        ("GMS","AE"): lambda df_num, df_cat: (df_num[df_num["item"].isin([1, 3, 8, 15, 24, 28])]["response"].sum() +
                                     (8 - df_num[df_num["item"].isin([21])]["response"]).sum() +
                                      sum([gsm_cat[item_cat].index(df_cat.loc[df_cat["item"].isin([item_cat])]["response"].values[0]) + 1 
                                           for item_cat in [34,38] ])),
                                           
        ("GMS", "PA"): lambda df_num, _: (df_num.loc[df_num["item"].isin([5, 6, 12, 18, 22, 26])]["response"].sum() +
                                      (8- df_num.loc[df_num["item"].isin([11, 13, 23])]["response"]).sum() ),

        ("GMS", "MT"): lambda df_num, df_cat: ((8 - df_num[df_num["item"].isin([14, 27])]["response"]).sum() +
                                      sum([gsm_cat[item_cat].index(df_cat.loc[df_cat["item"].isin([item_cat])]["response"].values[0]) + 1 
                                           for item_cat in [32, 33, 35, 36, 37] ])),


        ("GMS", "SA"): lambda df_num, _: (df_num.loc[df_num["item"].isin([4, 7, 10, 29, 30])]["response"].sum() +
                                      (8- df_num.loc[df_num["item"].isin([17, 25])]["response"]).sum() ),

        ("GMS", "EMO"): lambda df_num, _: (df_num.loc[df_num["item"].isin([2, 16, 19, 20, 31])]["response"].sum() +
                                      (8- df_num.loc[df_num["item"].isin([9])]["response"]).sum() ),

        ("GMS", "GS"): lambda df_num, df_cat: (df_num[df_num["item"].isin([1, 3, 4, 7, 10, 12, 15, 19, 24, 29])]["response"].sum() +
                                     (8 - df_num[df_num["item"].isin([14, 17, 23, 25, 27])]["response"]).sum() +
                                      sum([gsm_cat[item_cat].index(df_cat.loc[df_cat["item"].isin([item_cat])]["response"].values[0]) + 1 
                                           for item_cat in [32,33,37] ])),
    }

    # Separate categorical and numerical items in different dataframes
    df_grouped_num = df_grouped.sort_values(by="item").iloc[:-8].copy()
    df_grouped_num["response"] = df_grouped_num["response"].astype(int)
    df_grouped_cat = df_grouped.sort_values(by="item").iloc[-8:-1].copy()

    #Calculate scores
    scores = {dimension: score_func(df_grouped_num, df_grouped_cat) for dimension, score_func in gms_scores.items()}

    return scores


