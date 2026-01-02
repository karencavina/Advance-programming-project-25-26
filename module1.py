#Imports Section
'''Bringing in everything we need'''

import gzip #Reads and writes .gz compressed files

from typing import Iterable #We will use this for opening files and telling Python that they are strings

from dataclasses import dataclass #Skips defining the init method by having Python generate it for us

import pandas as pd #Helps with parsing information and building dataframes


#Creating DataBundle Class
''' This will help us organize the annotations'''

@dataclass(frozen=True) #Decorator that creates init method automatically
class DataBundle: #We create a class to act as a bundle that holds 3 dataframes
    terms_df: pd.DataFrame #Provides type hints
    edges_df: pd.DataFrame #Stores parent-child relationships
    annotations_df: pd.DataFrame #Stores annotations


#Opening Files
'''This opens the text file'''
'''The first return handles compressed files, the second non compressed ones'''

def _open_text_file(path: str) -> Iterable[str]: #Private method to open the file that specifies it is looking for strings
    if path.endswith(".gz"): #Checks if the file is compressed
        return gzip.open(path, mode="rt", encoding="utf-8", errors="replace")
    return open(path, mode="rt", encoding="utf-8", errors="replace")

'''mode="rt" means we are reading it as text'''
'''encoding="utf-8" tells the program how to interpret the tex (utf-8 is standard encoding)'''
'''errors="replace" replaces unreadable characters with a placeholder so the program does not crash'''



#Turning annotation file into pandas dataframe
'''This section will turn the input (gene annotation file) into a dataframe, courtesy of pandas'''

GAF_COLUMNS = [ "db", "db_object_id", "db_object_symbol", "qualifier", "go_id", "db_reference", "evidence_code", "with_from", "aspect", "db_object_name", "db_object_synonym", "db_object_type", "taxon", "date", "assigned_by", "annotation_extension", "gene_product_form_id", ]

'''Above we create a list of strings we will use to define the columns'''

def parse_gaf(path: str) -> pd.DataFrame: #Input a string, output a pandas dataframe
    rows = [] #Empty list for rows

    with _open_text_file(path) as f: #Remember we defined this above
        for line in f: #Goes through the file line by line
            if not line or line.startswith("!"): #Typically headers start with "!" so we skip these lines
                continue

            parts = line.rstrip("\n").split("\t") #Remove newline character and split into list of columns. "parts" is now a nicely formatted list

            if len(parts) < len(GAF_COLUMNS): #Equalizes row length so pandas doesn't complain
                parts += [""] * (len(GAF_COLUMNS) - len(parts))

            rows.append(parts[:len(GAF_COLUMNS)]) #Add the row to our list, the split keeps only the content of our desired length

    df = pd.DataFrame(rows, columns=GAF_COLUMNS) #Convert list of rows into pandas table

    '''Cleanup section, removing extra spaces, dealing with broken rows, etc'''

    for col in ["db_object_id", "db_object_symbol", "go_id", "evidence_code", "aspect"]:
        df[col] = df[col].astype(str).str.strip() #Remove leading/trailing spaces that can cause errors

    df = df[(df["go_id"] != "") & (df["db_object_id"] != "")] #Keep only rows that are of interest (Containing gene id or GO id)
    return df #Self explanatory, returns the table!



#Producing 2 data frames with info on each term and relationships
'''This will read the file and produce 2 separate data frames'''

def parse_obo(path: str) -> tuple[pd.DataFrame, pd.DataFrame]: #Take in string, return 2 dataframes
    terms_rows = [] #Store a dictionary for each GO term
    edges_rows = [] #Store a dictionary for each relationship

    current = {} #Dictionary to hold the current term data
    parents = [] #Storing relationships found while reading
    in_term = False #Making sure we are inside a term

    def flush(): #Useful because we repeat the operations
        if "go_id" not in current: #Make sure we don't add empty rows
            return
        
        terms_rows.append({ #Uses content from 'current' to create a standardized row
            "go_id": current.get("go_id", ""),
            "name": current.get("name", ""),
            "namespace": current.get("namespace", ""),
            "definition": current.get("definition", ""),
            "is_obsolete": current.get("is_obsolete", False),
        })

        for parent_id, rel in parents: #Per relationship found, create new row in edges_row
            edges_rows.append({
                "child_id": current["go_id"],
                "parent_id": parent_id,
                "relation": rel,
            })
    
    with open(path, mode="rt", encoding="utf-8", errors="replace") as f: #Remember we've already explained this once, standard opening function
        for line in f:
            line = line.strip() #Remove empty characters from beginning/end

            if line == "": #Once we hit the end of the term stanza,
                if in_term:
                    flush() #Save it to our outputs
                    current, parents = {}, [] #Reset current term and relationships
                    in_term = False #We are no longer in a term
                continue #Move to next line

            if line == "[Term]": #The opposite, this is the process when we start a new term
                in_term = True
                current, parents = {}, []
                continue

            if line.startswith("[") and line != "[Term]": #Ignore things that aren't terms
                in_term = False
                continue

            if not in_term or ":" not in line: #Ignore irrelevant lines
                continue

            key, value = line.split(":", 1) #Splitting lines into keys and values
            value = value.strip()

            if key == "id": #Store GO id
                current["go_id"] = value
            
            elif key == "name": #Store term name
                current["name"] = value

            elif key == "namespace": #Store namespace
                current["namespace"] = value

            elif key == "def": #Make sure we only take the relevant part of a definition
                if value.startswith('"'):
                    end = value.find('"', 1)
                    current["definition"] = value[1:end]
                else:
                    current["definition"] = value
            
            elif key == "is_obsolete": #Either true or false
                current["is_obsolete"] = (value.lower() == "true")
            
            elif key == "is_a": #Parent term indicator
                parent = value.split("!")[0].strip()
                parents.append((parent, "is_a"))

            elif key == "relationship": #Relationship indicator
                parts = value.split()
                if len(parts) >= 2:
                    parents.append((parts[1], parts[0])) #Store parent id and relation
            
    if in_term: #We save any term even if the file ends
        flush()

    return pd.DataFrame(terms_rows), pd.DataFrame(edges_rows) #Convert the lists of dictionaries we made into pandas dataframes



#Catching errors and proofreading
'''Making sure we don't have mistakes creeping in'''

def validate_all(terms_df: pd.DataFrame, #If everything is fine this function is silent
                 edges_df: pd.DataFrame, #Takes in the relevant dataframes
                 annotations_df: pd.DataFrame) -> None:
    if terms_df["go_id"].duplicated().any(): #We check for any duplicate IDs
        raise ValueError("Duplicate GO IDs found")
    
    term_ids = set(terms_df["go_id"]) #We make a set with all GO IDs for easier/faster checking
    if not edges_df["child_id"].isin(term_ids).all(): #Checking if all child IDs are valid GO IDs
        raise ValueError("Edges reference unknown child terms")
    
    if not annotations_df["go_id"].isin(term_ids).all(): #Making sure each annotation is connected to a GO ID
        raise ValueError("Annotations reference unknown GO terms")
    


#The function that ties it all together
'''This is the function that you guys are going to call'''

def load_all(obo_path: str, #Load everything and validate it
             gaf_path: str,
             *,
             validate: bool = True) -> DataBundle:
    
    terms_df, edges_df = parse_obo(obo_path) #We go through the ontology (term data and relationships)
    annotations_df = parse_gaf(gaf_path) #We go through annotations

    if validate: #If you asked for validation when calling the function, this line fires
        validate_all(terms_df, edges_df, annotations_df) #Proofreading

    return DataBundle( #At last, create and return a databundle
        terms_df=terms_df,
        edges_df=edges_df,
        annotations_df=annotations_df,
    )
