# Feed adapters — aggregate job boards with public APIs or RSS, as
# opposed to sources/ which read a specific company's ATS board.
# Feeds cast a wide net across companies you've never heard of; the
# watchlist filters do the narrowing. Each adapter exposes
# fetch(arg) -> list[dict] in the same normalized shape as sources/:
#   { company, source, id, title, location, remote, url, posted,
#     description, department }
# `arg` is the optional category from the watchlist entry, e.g.
# "- remotive (design)". Adapters return [] on any failure.


def get_feeds():
    from . import remotive, remoteok, weworkremotely, usajobs, neogov
    return {
        "remotive": remotive,
        "remoteok": remoteok,
        "weworkremotely": weworkremotely,
        "usajobs": usajobs,
        "neogov": neogov,
    }
