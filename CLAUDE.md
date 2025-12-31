j'ai 4 fichiers excel nommés : testa.xlsx, testb.xlsx, testc.xlsx et testd.xlsx dans un dossier actuellement. Plus tard les fichiers excel seront
probablement sur un sharepoint et donc la location doit être générique pour pouvoir
facilement prendre depuis un sharepoint plus tard.
Chaque fichier excel correspond à une liste de l'agence européenne des substances chimiques : 
 - liste d'authorisation
 - liste chls
 - liste restriction
 - ...

Le fichier testa.xlsx a pour structure :
cas_id,cas_name,info_a_1,info_a_2,info_a_3,info_a_4,info_a_5,info_a_6,info_a_7,info_a_8,info_a_9

le fichier testb.xlsx a pour structure : 
cas_id,cas_name,info_b_1,info_b_2,info_b_3,info_b_4,info_b_5,info_b_6,info_b_7,info_b_8,info_b_9

Le fichier testc.xlsx a pour structure : 
cas_id,cas_name,info_c_1,info_c_2,info_c_3,info_c_4,info_c_5,info_c_6,info_c_7,info_c_8,info_c_9

Le fichier testd.xlsx a pour structure : 
cas_id,cas_name,info_d_1,info_d_2,info_d_3,info_d_4,info_d_5,info_d_6,info_d_7,info_d_8,info_d_9

Tous les jours ou toutes les semaines (la fréquence n'est pas définie encore donc cela doit être facilement modifiable)
Les 4 fichiers excel sont retéléchargés depuis le site ECHA (agence européenne des substances chimiques) et les anciens fichiers sont archivés ou supprimés (à voir ce qui est le mieux).

A chaque mis à jour des 4 fichiers excel on peut avoir plusieurs situations : 
	- Une substance chimique est supprimé d'une liste
	- Une substance chimique est insérée dans une liste
	- Une substance chimique voit ses informations mises à jour

Il faudrait donc peut être créé un fichier excel aggrégeant toutes les données et un autre fichier excel contenant l'historique des modifications / suppressions / insertions.
Je te laisse voir ce qui est le mieux à faire.

L'utilisateur veut un tableau de bord steamlit où
	- Il peut visualiser chaque substance chimique avec toutes les informations disponibles dans les listes. L'idéal serait d'avoir un tableau aggrégeant les 15 listes et une colonne liste source pour savoir à quelle liste appartient une ligne). En sachant qu'une substance chimique peut être dans plusieurs liste.
	- Il veut pouvoir filtrer sur les noms de susbstance chimique et sur le col_cas (identifiant unique)
	- Il veut être alerté dans le tableau de bord (peut être un tableau à part) pour chaque insertion / suppression / modification de chaque liste)

En plus de ces 4 fichiers correspondant à chaque liste, on a une base principale des substances chimiques avec les colonnes cas_id et cas_name. Cette base principale
se trouve dans un fichier excel à part nommé cas_source.xlsx) et on part du principe qu'elle est statique.
On suppose que chaque substance dans les 15 fichiers excels des listes ECHA existent dans la base principale (fichier cas_source.xlsx).

Il faudrait faire un script python pour répondre à ce besoin. Ce script python doit être modulaire (plusieurs fichiers pythons) et le code doit être simple en terme de complexité cyclomatique.
Est-ce que tu penses que la librairie DLT est bien dans ce cas ?
Et explique moi en détail comment tu comptes t'y prendre pour répondre à ce besoin (sans me donner de code).

Une contrainte supplémentaire est la suivante : les noms de colonnes de tous les fichiers excel sont fictifs actuellement. Il faut donc créér un fichier de config contenant les noms de colonnes pour pouvoir les changer plus tard facilement si besoin. Ou bien je te laisse voir ce qui est le mieux à faire pour répondre à cette contrainte.


