import csv
import itertools
import sys

PROBS = {

    # Unconditional probabilities for having gene
    "gene": {
        2: 0.01,
        1: 0.03,
        0: 0.96
    },

    "trait": {

        # Probability of trait given two copies of gene
        2: {
            True: 0.65,
            False: 0.35
        },

        # Probability of trait given one copy of gene
        1: {
            True: 0.56,
            False: 0.44
        },

        # Probability of trait given no gene
        0: {
            True: 0.01,
            False: 0.99
        }
    },

    # Mutation probability
    "mutation": 0.01
}


def main():

    # Check for proper usage
    if len(sys.argv) != 2:
        sys.exit("Usage: python heredity.py data.csv")
    people = load_data(sys.argv[1])

    # Keep track of gene and trait probabilities for each person
    probabilities = {
        person: {
            "gene": {
                2: 0,
                1: 0,
                0: 0
            },
            "trait": {
                True: 0,
                False: 0
            }
        }
        for person in people
    }

    # Loop over all sets of people who might have the trait
    names = set(people)
    for have_trait in powerset(names):

        # Check if current set of people violates known information
        fails_evidence = any(
            (people[person]["trait"] is not None and
             people[person]["trait"] != (person in have_trait))
            for person in names
        )
        if fails_evidence:
            continue

        # Loop over all sets of people who might have the gene
        for one_gene in powerset(names):
            for two_genes in powerset(names - one_gene):

                # Update probabilities with new joint probability
                p = joint_probability(people, one_gene, two_genes, have_trait)
                update(probabilities, one_gene, two_genes, have_trait, p)

    # Ensure probabilities sum to 1
    normalize(probabilities)

    # Print results
    for person in people:
        print(f"{person}:")
        for field in probabilities[person]:
            print(f"  {field.capitalize()}:")
            for value in probabilities[person][field]:
                p = probabilities[person][field][value]
                print(f"    {value}: {p:.4f}")


def load_data(filename):
    """
    Load gene and trait data from a file into a dictionary.
    File assumed to be a CSV containing fields name, mother, father, trait.
    mother, father must both be blank, or both be valid names in the CSV.
    trait should be 0 or 1 if trait is known, blank otherwise.
    """
    data = dict()
    with open(filename) as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"]
            data[name] = {
                "name": name,
                "mother": row["mother"] or None,
                "father": row["father"] or None,
                "trait": (True if row["trait"] == "1" else
                          False if row["trait"] == "0" else None)
            }
    return data


def powerset(s):
    """
    Return a list of all possible subsets of set s.
    """
    s = list(s)
    return [
        set(s) for s in itertools.chain.from_iterable(
            itertools.combinations(s, r) for r in range(len(s) + 1)
        )
    ]


def number_of_copies(person, one_gene, two_genes):
    """
    Checks the number of copies given a person
    """
    if person in one_gene:
        return 1

    if person in two_genes:
        return 2

    return 0


def no_parents_probs(gene_copies, trait):
    return PROBS["gene"][gene_copies] * PROBS["trait"][gene_copies][trait]


def parents_probs(person, people, one_gene, two_genes):
    child_genes = number_of_copies(person, one_gene, two_genes)

    mother = people[person]["mother"]
    mother_genes = number_of_copies(mother, one_gene, two_genes)

    father = people[person]["father"]
    father_genes = number_of_copies(father, one_gene, two_genes)

    # Probability that mother passes a gene (considering mutation)
    mother_passes = (mother_genes / 2) * \
        (1 - PROBS["mutation"]) + (1 - mother_genes / 2) * PROBS["mutation"]
    
    # Probability that father passes a gene (considering mutation)
    father_passes = (father_genes / 2) * \
        (1 - PROBS["mutation"]) + (1 - father_genes / 2) * PROBS["mutation"]

    probability = 0

    if child_genes == 0:
        # Child gets no genes from either parent
        probability = (1 - mother_passes) * (1 - father_passes)
    elif child_genes == 1:
        # Child gets one gene from either parent
        probability = mother_passes * (1 - father_passes) + (1 - mother_passes) * father_passes
    elif child_genes == 2:
        # Child gets genes from both parents
        probability = mother_passes * father_passes

    return probability


def joint_probability(people, one_gene, two_genes, have_trait):
    """
    Compute and return a joint probability.

    The probability returned should be the probability that
        * everyone in set `one_gene` has one copy of the gene, and
        * everyone in set `two_genes` has two copies of the gene, and
        * everyone not in `one_gene` or `two_gene` does not have the gene, and
        * everyone in set `have_trait` has the trait, and
        * everyone not in set` have_trait` does not have the trait.
    """
    probability = 1

    for person in people:
        gene_copies = number_of_copies(person, one_gene, two_genes)
        trait = person in have_trait

        if people[person]["mother"] is None and people[person]["father"] is None:
            # No parents, use unconditional probabilities
            probability *= PROBS["gene"][gene_copies] * PROBS["trait"][gene_copies][trait]
        else:
            # Has parents, calculate gene inheritance probability
            gene_prob = parents_probs(person, people, one_gene, two_genes)
            trait_prob = PROBS["trait"][gene_copies][trait]
            probability *= gene_prob * trait_prob

    return probability


def update(probabilities, one_gene, two_genes, have_trait, p):
    """
    Add to `probabilities` a new joint probability `p`.
    Each person should have their "gene" and "trait" distributions updated.
    Which value for each distribution is updated depends on whether
    the person is in `have_gene` and `have_trait`, respectively.
    """
    for person in probabilities:
        gene_copies = number_of_copies(person, one_gene, two_genes)

        if person in have_trait:
            trait = True 
        else: 
            trait = False

        probabilities[person]["gene"][gene_copies] += p
        probabilities[person]["trait"][trait] += p

    return probabilities


def normalize(probabilities):
    """
    Update `probabilities` such that each probability distribution
    is normalized (i.e., sums to 1, with relative proportions the same).
    """
    for person in probabilities:
        total_p_genes = sum(probabilities[person]["gene"].values())
        total_p_traits = sum(probabilities[person]["trait"].values())

        for gene in probabilities[person]["gene"]:
            value = probabilities[person]["gene"][gene]
            new_value = value / total_p_genes
            probabilities[person]["gene"][gene] = new_value

        for trait in probabilities[person]["trait"]:
            value = probabilities[person]["trait"][trait]
            new_value = value / total_p_traits
            probabilities[person]["trait"][trait] = new_value


if __name__ == "__main__":
    main()
