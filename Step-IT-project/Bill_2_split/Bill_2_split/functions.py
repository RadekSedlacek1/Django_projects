def get_relation_value(obj):
    return obj.relation

def calculate_relation_costs(relations, cost):
    # 1. Určení pořadí od největšího relation po nejmenší
    sorted_relations = sorted(relations, key=get_relation_value, reverse=True)

    # 2. Vynásobení každé hodnoty relation s hodnotou cost
    relation_costs = [(relation, relation.relation * cost) for relation in sorted_relations]

    return relation_costs