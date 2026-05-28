from jinja2 import Template

# simulating dictionary
items = [{'meal_slot': 'lunch', 'items': 'Rice'}]

t = Template("{% set m = items | selectattr('meal_slot', 'equalto', 'lunch') | list %}{{m}}")
print(t.render(items=items))
