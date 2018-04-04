import jq
from jsonmapping.value import is_empty, convert_value
from .transform import FILTER_NULL, apply_transformations


def filter_null(value):
    return jq.jq(FILTER_NULL).transform(value)


def _get_source(mapper, bind):
    mapping = getattr(mapper, 'mapping', mapper)
    if not mapping.get('src') and mapping.get('default'):
        return True, mapping.get('default')
    src = mapping.get(
        'src', '.{}'.format(bind.name)
    )
    if isinstance(src, (list, tuple)):

        sources = [
            value if value.startswith('.') else '.{}'.format(value)
            for value in src
        ]
    else:
        sources = src if src.startswith('.') else '.{}'.format(src)
    return (False, sources)


def extract_array(mapper, bind, data):

    def extract(iterator):
        result = []
        if not isinstance(iterator, list):
            iterator = [iterator]
        for item in iterator:
            got = mapper.apply(item)
            if isinstance(got, list):
                result.extend(got)
            else:
                result.append(got)
        return result

    default, value = _get_source(mapper, bind)
    # TODO: test for default array
    if default:
        return value
    if isinstance(value, list):
        result = []
        for source in value:
            result.extend(extract(jq.jq(source).transform(data)))
    else:
        result = extract(jq.jq(value).transform(data))
    return apply_transformations(
        mapper.mapping,
        bind,
        [item for item in result if item]
        )


def extract_value(mapping, bind, data):
    """ Given a mapping and JSON schema spec, extract a value from ``data``
    and apply certain transformations to normalize the value. """
    default, src = _get_source(mapping, bind)
    if default:
        return src
    if isinstance(data, dict):  # TODO: test me
        value = jq.jq(src).transform(data)
    else:
        value = data
    value = apply_transformations(mapping, bind, value)
    empty = is_empty(value)
    if empty:
        value = mapping.get('default') or bind.schema.get('default')
    return value
    # TODO: breaks json serialization
    # return convert_value(bind, value)
