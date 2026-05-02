"""
`python manage.py seed_database`

Seeds all 25 Sri Lankan districts with real, curated attractions (no
placeholder rows). Each attraction gets a Wikipedia page title that the
`fetch_wikimedia_images` command later uses to pull real photography.

Re-run safely: `--flush` wipes attractions/districts before seeding.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from apps.attractions.models import (
    Attraction,
    AttractionCategory,
    ClimateZone,
    District,
    MediaAsset,
)

# ─────────────────────────── Districts ─────────────────────────────────
DISTRICTS: list[dict] = [
    {"name": "Colombo", "province": "Western", "lat": 6.9271, "lng": 79.8612, "climate": ClimateZone.WET, "peak": [12, 1, 2, 3, 7, 8], "yt": ["7e8VC9q3-cI", "ZZ7vbZB7Z3w", "wnkcwS9-CBg"], "desc": "Sri Lanka's commercial capital — colonial-era streets, modern skyline, food markets and a 350-metre observation tower."},
    {"name": "Gampaha", "province": "Western", "lat": 7.0917, "lng": 79.9999, "climate": ClimateZone.WET, "peak": [12, 1, 2, 3], "yt": ["WUyB-O5Tnyk"], "desc": "Greater Colombo's leafy hinterland — Henarathgoda Botanical Gardens, river cruises and rural Buddhist heritage."},
    {"name": "Kalutara", "province": "Western", "lat": 6.5854, "lng": 79.9607, "climate": ClimateZone.WET, "peak": [12, 1, 2, 3], "yt": ["uYy0yVWzG6Q"], "desc": "Coast-and-river district just south of Colombo — the Kalutara Bodhi shrine, river-mouth surfing and palm-lined beaches."},
    {"name": "Kandy", "province": "Central", "lat": 7.2906, "lng": 80.6337, "climate": ClimateZone.INTERMEDIATE, "peak": [1, 2, 3, 7, 8], "yt": ["Gj6cxvrL2u4", "Hb8a2L1zXkE", "S6XKLR2tPvY"], "desc": "The hill-country royal capital and home of the Sacred Tooth Relic — temples, lake walks, and the Esala Perahera pageant."},
    {"name": "Matale", "province": "Central", "lat": 7.4675, "lng": 80.6234, "climate": ClimateZone.INTERMEDIATE, "peak": [5, 6, 7, 8, 9], "yt": ["G37oTtH5KdM", "kzZ5fTDHM8E"], "desc": "The cultural triangle's gateway — Sigiriya, Dambulla cave temple, spice gardens and ancient Buddhist sites."},
    {"name": "Nuwara Eliya", "province": "Central", "lat": 6.9497, "lng": 80.7891, "climate": ClimateZone.INTERMEDIATE, "peak": [1, 2, 3, 4, 8], "yt": ["fZsVdGhTYxw", "KqYwEksjVTI"], "desc": "'Little England' — colonial bungalows at 1,900 m, mist-soaked tea estates, Horton Plains and Gregory Lake."},
    {"name": "Galle", "province": "Southern", "lat": 6.0535, "lng": 80.2210, "climate": ClimateZone.WET, "peak": [11, 12, 1, 2, 3], "yt": ["U_QeXvWY7Ng", "B5nBqV2pJ8I"], "desc": "UNESCO-walled Dutch fort, surf coves, turtle beaches and the south coast's most photogenic stretch."},
    {"name": "Matara", "province": "Southern", "lat": 5.9485, "lng": 80.5353, "climate": ClimateZone.WET, "peak": [12, 1, 2, 3, 4], "yt": ["XcANUuvFqfY"], "desc": "Mirissa's whales and surf, Weherahena temple, Polhena snorkelling and the Star Fort."},
    {"name": "Hambantota", "province": "Southern", "lat": 6.1241, "lng": 81.1185, "climate": ClimateZone.DRY, "peak": [2, 3, 4, 5, 6, 7], "yt": ["UMpV5lzRnVk"], "desc": "Yala safari country, salt pans, Bundala wetlands and the dry-zone south coast — leopards, elephants and flamingos."},
    {"name": "Jaffna", "province": "Northern", "lat": 9.6615, "lng": 80.0255, "climate": ClimateZone.DRY, "peak": [5, 6, 7, 8, 9], "yt": ["7DJVqz2N6F4"], "desc": "Tamil cultural heartland — Nallur Kovil, Dutch fort, the islands of Karaitivu and the long causeway to Delft."},
    {"name": "Kilinochchi", "province": "Northern", "lat": 9.3961, "lng": 80.4036, "climate": ClimateZone.DRY, "peak": [5, 6, 7, 8], "yt": ["7DJVqz2N6F4", "sXCDNk8lh-A"], "desc": "Inland Northern district rebuilding after the war — Iranamadu tank, palmyra plantations and lesser-visited temples."},
    {"name": "Mannar", "province": "Northern", "lat": 8.9810, "lng": 79.9047, "climate": ClimateZone.DRY, "peak": [5, 6, 7, 8], "yt": ["7DJVqz2N6F4", "kZpkmJ72eeA"], "desc": "Bridge of Adam's Bridge / Rama's Setu, baobab trees, wild donkeys and Talaimannar's lighthouse on the Indian crossing."},
    {"name": "Vavuniya", "province": "Northern", "lat": 8.7514, "lng": 80.4971, "climate": ClimateZone.DRY, "peak": [5, 6, 7, 8], "yt": ["7DJVqz2N6F4", "BiP8njLE4uY"], "desc": "Crossroads town between the cultural triangle and Jaffna — tanks, Madhu road and quiet rural Buddhism."},
    {"name": "Mullaitivu", "province": "Northern", "lat": 9.2671, "lng": 80.8142, "climate": ClimateZone.DRY, "peak": [5, 6, 7, 8], "yt": ["bDH5Wq6hI3I", "kZpkmJ72eeA"], "desc": "The eastern Vanni coast — pristine beaches at Nayaru, Nanthikadal lagoon and one of the country's wildest stretches."},
    {"name": "Batticaloa", "province": "Eastern", "lat": 7.7170, "lng": 81.7000, "climate": ClimateZone.DRY, "peak": [4, 5, 6, 7, 8, 9], "yt": ["bDH5Wq6hI3I"], "desc": "Sun-drenched east-coast town with a Dutch fort, lagoon kallady bridge, and Pasikudah's bath-warm reef beach."},
    {"name": "Ampara", "province": "Eastern", "lat": 7.2916, "lng": 81.6747, "climate": ClimateZone.DRY, "peak": [5, 6, 7, 8, 9], "yt": ["bDH5Wq6hI3I", "kZpkmJ72eeA", "UMpV5lzRnVk"], "desc": "Eastern wildlife and surf — Arugam Bay's point break, Lahugala's elephants and Buddhangala's hilltop forest temple."},
    {"name": "Trincomalee", "province": "Eastern", "lat": 8.5874, "lng": 81.2152, "climate": ClimateZone.DRY, "peak": [4, 5, 6, 7, 8, 9], "yt": ["kZpkmJ72eeA"], "desc": "Natural deep-water harbour, Hindu pilgrimage at Koneswaram, blue whales offshore and Nilaveli's white sand."},
    {"name": "Kurunegala", "province": "North Western", "lat": 7.4863, "lng": 80.3623, "climate": ClimateZone.INTERMEDIATE, "peak": [1, 2, 3, 7, 8], "yt": ["sXCDNk8lh-A", "BiP8njLE4uY", "G37oTtH5KdM"], "desc": "Coconut triangle gateway — Yapahuwa rock fortress, Athugala 'elephant rock' and Panduwasnuwara medieval ruins."},
    {"name": "Puttalam", "province": "North Western", "lat": 8.0408, "lng": 79.8394, "climate": ClimateZone.DRY, "peak": [2, 3, 4, 5, 6, 7], "yt": ["UMpV5lzRnVk", "sXCDNk8lh-A", "kZpkmJ72eeA"], "desc": "Wilpattu safari country, salt-pan flamingos at Kalpitiya, kitesurfing lagoon and Munneswaram pilgrimages."},
    {"name": "Anuradhapura", "province": "North Central", "lat": 8.3114, "lng": 80.4037, "climate": ClimateZone.DRY, "peak": [5, 6, 7, 8, 9], "yt": ["sXCDNk8lh-A"], "desc": "Sri Lanka's first ancient capital and a UNESCO sacred city — colossal stupas, the Sri Maha Bodhi tree, Ritigala forest."},
    {"name": "Polonnaruwa", "province": "North Central", "lat": 7.9403, "lng": 81.0188, "climate": ClimateZone.DRY, "peak": [5, 6, 7, 8, 9], "yt": ["BiP8njLE4uY"], "desc": "The medieval royal capital, UNESCO listed — Gal Vihara's reclining Buddha, Parakrama Samudra and Minneriya elephants."},
    {"name": "Badulla", "province": "Uva", "lat": 6.9934, "lng": 81.0550, "climate": ClimateZone.INTERMEDIATE, "peak": [1, 2, 3, 4, 8], "yt": ["67gz8PxTI3Y", "sJW6V8hjYjA"], "desc": "Ella, Lipton's seat, Nine Arches viaduct and the most loved hill-country backpacker valley in Sri Lanka."},
    {"name": "Moneragala", "province": "Uva", "lat": 6.8714, "lng": 81.3506, "climate": ClimateZone.DRY, "peak": [5, 6, 7, 8], "yt": ["UMpV5lzRnVk", "67gz8PxTI3Y", "sJW6V8hjYjA"], "desc": "Wild-east province — Maligawila's giant standing Buddha, Kataragama pilgrim road and Yala's quieter eastern boundary."},
    {"name": "Ratnapura", "province": "Sabaragamuwa", "lat": 6.6828, "lng": 80.3992, "climate": ClimateZone.WET, "peak": [1, 2, 3, 7, 8], "yt": ["fZsVdGhTYxw", "KqYwEksjVTI", "Hb8a2L1zXkE"], "desc": "'City of Gems' — Sinharaja rainforest, Adam's Peak's southern trail and gem-mining lore."},
    {"name": "Kegalle", "province": "Sabaragamuwa", "lat": 7.2513, "lng": 80.3464, "climate": ClimateZone.INTERMEDIATE, "peak": [1, 2, 3, 7, 8], "yt": ["Gj6cxvrL2u4", "S6XKLR2tPvY", "WUyB-O5Tnyk"], "desc": "Pinnawala elephant orphanage, Bible Rock (Bathalegala), Utuwankanda outlaw legends and tea-plus-rubber estates."},
]


# ─────────────────────────── Attractions ───────────────────────────────
# Each entry: (name, category, fee_lkr, season, trend, description, wikipedia_title)
def _att(name, cat, fee, season, trend, desc, wiki=None, yt=""):
    return {
        "name": name,
        "category": cat,
        "fee": fee,
        "season": season,
        "trend": trend,
        "desc": desc,
        "wiki": wiki or name,
        "yt": yt,
    }


CULT = AttractionCategory.CULTURAL
RELI = AttractionCategory.RELIGIOUS
WILD = AttractionCategory.WILDLIFE
BEAC = AttractionCategory.BEACH
ADVE = AttractionCategory.ADVENTURE
FOOD = AttractionCategory.FOOD

ATTRACTIONS: dict[str, list[dict]] = {
    "Colombo": [
        _att("Gangaramaya Temple", RELI, 500, [1, 2, 3, 7, 8, 12], 8.4, "Eclectic urban temple complex blending Sri Lankan, Thai, Indian and Chinese architecture, with a museum of priceless jade and ivory donations.", "Gangaramaya Temple"),
        _att("Galle Face Green", CULT, 0, list(range(1, 13)), 7.6, "A 500-metre seafront promenade beloved for sunset walks, kite-flying and street food.", "Galle Face Green"),
        _att("National Museum of Colombo", CULT, 1000, list(range(1, 13)), 6.8, "The country's largest museum, housing the Kandyan king's regalia and 5,000 years of artifacts.", "Colombo National Museum"),
        _att("Pettah Market", FOOD, 0, list(range(1, 13)), 7.2, "Sprawling commercial bazaar with spice, fruit, fabric and electronics streets.", "Pettah"),
        _att("Dutch Hospital Shopping Precinct", CULT, 0, list(range(1, 13)), 7.0, "Restored 17th-century hospital now hosting cafes, boutiques and rooftop bars.", "Dutch Hospital, Colombo"),
        _att("Beira Lake", CULT, 0, list(range(1, 13)), 6.4, "Central-city lake with swan boats and the floating Seema Malaka temple.", "Beira Lake"),
        _att("Independence Memorial Hall", CULT, 0, list(range(1, 13)), 6.6, "Granite open-air assembly modelled on the Royal Audience Hall of Kandy, marking 1948 independence.", "Independence Memorial Hall"),
        _att("Viharamahadevi Park", CULT, 0, list(range(1, 13)), 6.2, "Colombo's oldest and largest park, named for the mother of King Dutugamunu.", "Viharamahadevi Park"),
        _att("Mount Lavinia Beach", BEAC, 0, [11, 12, 1, 2, 3], 7.4, "Closest beach resort to Colombo, famed for its colonial-era hotel and Sunday seafood.", "Mount Lavinia"),
        _att("Lotus Tower Observation Deck", ADVE, 2500, list(range(1, 13)), 8.0, "South Asia's tallest self-supported tower; observation deck at 350 m gives panoramic city views.", "Lotus Tower"),
    ],
    "Gampaha": [
        _att("Henarathgoda Botanical Gardens", CULT, 600, list(range(1, 13)), 6.8, "44-hectare gardens that pioneered Sri Lanka's rubber industry; oldest planted rubber tree on the island stands here.", "Henarathgoda Botanic Gardens"),
        _att("Kelaniya Raja Maha Vihara", RELI, 0, list(range(1, 13)), 7.4, "One of Sri Lanka's most sacred Buddhist temples, said to have been visited by the Buddha himself; Solias Mendis murals.", "Kelaniya Raja Maha Vihara"),
        _att("Negombo Lagoon", WILD, 0, list(range(1, 13)), 7.0, "Mangrove-fringed lagoon with traditional outrigger canoes and birding boat tours.", "Negombo Lagoon"),
        _att("Negombo Beach", BEAC, 0, [11, 12, 1, 2, 3], 7.2, "Fishing-village beach 10 minutes from the international airport — handy first or last stop on any Sri Lanka trip.", "Negombo"),
        _att("Muthurajawela Wetland", WILD, 800, [1, 2, 3, 11, 12], 6.4, "Coastal marsh teeming with kingfishers, water monitors and crocodiles, explored by quiet boat.", "Muthurajawela"),
        _att("Attanagalla Raja Maha Vihara", RELI, 0, list(range(1, 13)), 6.0, "Ancient royal temple linked to King Walagamba; Bo tree, dagoba and a peaceful tank.", "Attanagalla Raja Maha Vihara"),
    ],
    "Kalutara": [
        _att("Kalutara Bodhiya", RELI, 0, list(range(1, 13)), 7.4, "Towering hollow stupa with painted murals inside, beside the Kalu Ganga estuary; pilgrims pour offerings as they cross the bridge.", "Kalutara Bodhiya"),
        _att("Richmond Castle", CULT, 1000, list(range(1, 13)), 6.4, "1900s mansion combining British and Indian architecture, set in 100-year-old gardens.", "Richmond Castle, Sri Lanka"),
        _att("Kalutara Beach", BEAC, 0, [11, 12, 1, 2, 3], 7.2, "Long sweep of golden sand at the river mouth — popular for windsurfing and beach hotels.", "Kalutara"),
        _att("Bentota Beach", BEAC, 0, [11, 12, 1, 2, 3], 8.0, "South-coast resort beach famed for water sports on the Madu Ganga and turtle hatcheries.", "Bentota"),
        _att("Brief Garden", CULT, 1500, list(range(1, 13)), 7.0, "Bevis Bawa's lush sculpted garden — a tropical layered landscape carved out of a rubber estate.", "Brief Garden"),
        _att("Madu Ganga Mangrove Boat Safari", WILD, 1500, list(range(1, 13)), 7.2, "Two-hour Ramsar-listed estuary tour through cinnamon islands, fish-spa stops and mangrove tunnels.", "Madu Ganga"),
    ],
    "Kandy": [
        _att("Temple of the Sacred Tooth Relic", RELI, 1500, list(range(1, 13)), 9.2, "Sri Lanka's most venerated Buddhist temple, housing a relic of the Buddha's tooth in a gold and gem-encrusted casket.", "Sri Dalada Maligawa"),
        _att("Royal Botanical Gardens, Peradeniya", CULT, 2500, [1, 2, 3, 7, 8, 9], 8.4, "60-hectare 19th-century gardens with the world-renowned Avenue of Royal Palms and an orchid house.", "Royal Botanical Gardens, Peradeniya"),
        _att("Kandy Lake", CULT, 0, list(range(1, 13)), 7.0, "Artificial lake built in 1807 by the last king of Kandy, ringed by an easy walking path with herons and monitor lizards.", "Kandy Lake"),
        _att("Bahirawakanda Vihara Buddha Statue", RELI, 250, list(range(1, 13)), 7.2, "26-metre seated Buddha overlooking Kandy from the western hills; sunset views over the lake.", "Bahirawakanda Vihara Buddha Statue"),
        _att("Udawatta Kele Forest Reserve", WILD, 700, [1, 2, 3, 7, 8, 9], 6.6, "Royal forest immediately north of the Tooth Temple, home to monkeys, monitor lizards and 80+ bird species.", "Udawatta Kele Sanctuary"),
        _att("Ceylon Tea Museum", CULT, 1000, list(range(1, 13)), 6.8, "Hantana hilltop museum tracing the rise of Sri Lanka's signature export with antique machinery.", "Ceylon Tea Museum"),
        _att("Kandyan Cultural Centre Dance Show", CULT, 1500, list(range(1, 13)), 7.6, "Nightly showcase of Kandyan dance, fire-walking and traditional drumming.", "Kandyan dance"),
        _att("Embekka Devalaya", RELI, 500, list(range(1, 13)), 6.4, "14th-century devale celebrated for the wood-carving virtuosity of its drummers' hall.", "Embekka Devalaya"),
        _att("Knuckles Mountain Range", ADVE, 2500, [1, 2, 3, 7, 8], 8.0, "UNESCO-listed range offering multi-day treks through cloud forest and montane grassland.", "Knuckles Mountain Range"),
        _att("Esala Perahera Procession Route", CULT, 0, [7, 8], 8.8, "Annual 10-night procession of caparisoned elephants and Kandyan dancers; tickets sell out months ahead.", "Esala Perahera of Kandy"),
    ],
    "Matale": [
        _att("Sigiriya Rock Fortress", CULT, 6000, [1, 2, 3, 5, 6, 7, 8, 9], 9.6, "5th-century royal citadel atop a 200-metre granite column; UNESCO World Heritage site with frescoes and lion staircase.", "Sigiriya"),
        _att("Pidurangala Rock", ADVE, 1000, [1, 2, 3, 5, 6, 7, 8, 9], 8.8, "Adjacent rock with the iconic sunrise view of Sigiriya from the recumbent Buddha summit.", "Pidurangala"),
        _att("Dambulla Cave Temple", RELI, 2000, list(range(1, 13)), 8.4, "Five painted caves containing 153 statues of the Buddha; oldest murals date to the 1st century BCE.", "Dambulla cave temple"),
        _att("Aluvihare Rock Temple", RELI, 250, list(range(1, 13)), 6.6, "Where the Pali Tipitaka was first transcribed onto ola leaves in the 1st century BCE.", "Aluvihare Rock Temple"),
        _att("Sembuwatta Lake", ADVE, 600, [1, 2, 3, 7, 8], 6.4, "Crystalline reservoir set in tea country at 1,000 m, with kayaks and a 90-minute jungle walk.", "Sembuwatta Lake"),
        _att("Nalanda Gedige", CULT, 500, [1, 2, 3, 7, 8, 9], 6.0, "8th-century stone temple combining Hindu and Buddhist motifs; relocated stone-by-stone in the 1980s.", "Nalanda Gedige"),
        _att("Sera Ella Falls", ADVE, 200, [1, 2, 3, 4], 6.4, "Two-tier waterfall in Knuckles foothills; short forest walk to the base pool.", "Sera Ella"),
        _att("Riverston Mini World's End", ADVE, 0, [1, 2, 3, 7, 8], 6.8, "Cliff-edge plateau in the Knuckles range with a sheer 1,000-metre drop and 360-degree views.", "Riverston"),
    ],
    "Nuwara Eliya": [
        _att("Horton Plains National Park", WILD, 5000, [1, 2, 3, 4], 9.0, "High-elevation plateau with the cliff at World's End, Baker's Falls and rare endemic montane wildlife.", "Horton Plains National Park"),
        _att("Pedro Tea Estate", CULT, 1000, list(range(1, 13)), 7.4, "Working tea factory near Nuwara Eliya offering full process tours and high-grown tastings.", "Pedro Tea Estate"),
        _att("Gregory Lake", CULT, 250, list(range(1, 13)), 7.0, "Reservoir at the heart of Nuwara Eliya — pedal boats, lake-side picnic lawn and a sunset jogging path.", "Gregory Lake"),
        _att("Hakgala Botanical Garden", CULT, 1500, list(range(1, 13)), 6.8, "27-hectare highland garden under Hakgala rock, with rose terraces and cool-climate flora.", "Hakgala Botanical Garden"),
        _att("Adisham Hall", CULT, 500, list(range(1, 13)), 6.0, "1930s English country house turned Benedictine monastery; famed for its homemade jams and rose garden.", "Adisham"),
        _att("Lover's Leap Waterfall", ADVE, 0, [1, 2, 3, 4], 6.0, "30-metre fall a short walk above Nuwara Eliya — best after rain in the first quarter of the year.", "Lover's Leap (waterfall)"),
        _att("Single Tree Hill", ADVE, 0, [1, 2, 3, 7, 8], 6.4, "Easy 90-minute climb to a 360-degree viewpoint over Nuwara Eliya valley.", "Single Tree Hill"),
    ],
    "Galle": [
        _att("Galle Fort", CULT, 0, [11, 12, 1, 2, 3], 9.0, "UNESCO-listed Dutch-built fortified old town, walled, livable and impossibly photogenic.", "Galle Fort"),
        _att("Galle Lighthouse", CULT, 0, list(range(1, 13)), 7.4, "26-metre lighthouse inside Galle Fort; built by the British in 1939, still operational.", "Galle Lighthouse"),
        _att("Jungle Beach", BEAC, 0, [11, 12, 1, 2, 3], 7.6, "Sheltered cove a short tuk-tuk from Unawatuna with calm swimming and reef snorkelling.", "Jungle Beach"),
        _att("Unawatuna Beach", BEAC, 0, [11, 12, 1, 2, 3], 8.2, "Crescent of golden sand and warm shallows; one of the south coast's most loved beaches.", "Unawatuna"),
        _att("Sea Turtle Hatchery, Habaraduwa", WILD, 1000, list(range(1, 13)), 6.8, "Conservation centre where injured turtles recover; nightly hatchling releases in season.", "Sea turtle"),
        _att("Maritime Archaeology Museum", CULT, 800, list(range(1, 13)), 6.0, "Inside a Dutch-era warehouse: shipwreck artifacts and Indian Ocean trade history.", "Maritime Museum, Galle"),
        _att("Japanese Peace Pagoda", RELI, 0, list(range(1, 13)), 6.6, "White hilltop dagoba with sweeping views over Unawatuna bay; built by a Japanese Buddhist order.", "Peace Pagoda Stupa"),
        _att("Hiyare Reservoir & Rainforest", WILD, 600, [1, 2, 3, 7, 8], 6.4, "Quiet inland reservoir with a research station, rare endemic frogs and easy lakeside trails.", "Hiyare Reservoir"),
        _att("Kosgoda Beach", BEAC, 0, [11, 12, 1, 2, 3], 6.8, "Gold-sand stretch known for the largest concentration of turtle hatcheries on the island.", "Kosgoda"),
        _att("Stilt Fishermen of Koggala", CULT, 0, list(range(1, 13)), 7.0, "Iconic stilt-perched fishermen along the Galle-Matara coast; sunrise is the photogenic hour.", "Stilt fishing"),
    ],
    "Matara": [
        _att("Mirissa Beach", BEAC, 0, [11, 12, 1, 2, 3], 8.6, "Crescent of palm-fringed sand, world-famous for blue-whale watching and Coconut Tree Hill sunsets.", "Mirissa"),
        _att("Mirissa Whale Watching", WILD, 6000, [11, 12, 1, 2, 3, 4], 8.8, "Half-day boat trips that spot blue whales, sperm whales and acrobatic spinner dolphins.", "Whale watching in Sri Lanka"),
        _att("Polhena Reef", BEAC, 0, [11, 12, 1, 2, 3], 7.0, "Calm shallow reef with excellent snorkelling; turtles graze on seagrass meadows.", "Polhena"),
        _att("Star Fort, Matara", CULT, 600, list(range(1, 13)), 6.6, "Hexagonal Dutch fort built in 1765 inland of the main fort, now a small museum.", "Star Fort, Matara"),
        _att("Weherahena Buddhist Temple", RELI, 0, list(range(1, 13)), 6.4, "Painted tunnel temple beneath a 39-metre seated Buddha — Sri Lanka's largest concrete statue.", "Weherahena Temple"),
        _att("Dondra Head Lighthouse", CULT, 200, list(range(1, 13)), 7.4, "49-metre lighthouse at Sri Lanka's southernmost point, built in 1890.", "Dondra Head"),
        _att("Hummanaya Blowhole", ADVE, 200, [12, 1, 2, 3], 6.6, "Second-largest sea blowhole in the world, sending water 25 m skyward on swelly days.", "Hummanaya"),
    ],
    "Hambantota": [
        _att("Yala National Park", WILD, 6000, [2, 3, 4, 5, 6, 7], 9.4, "Sri Lanka's most famous safari park — highest density of wild leopards on Earth, plus elephants, sloth bears and crocodiles.", "Yala National Park"),
        _att("Bundala National Park", WILD, 4500, [9, 10, 11, 12, 1, 2, 3], 7.8, "Ramsar-listed coastal lagoons that host migratory flamingos, painted storks and waders.", "Bundala National Park"),
        _att("Kataragama Temple", RELI, 0, [7, 8], 8.4, "Multi-religion pilgrimage complex shared by Buddhists, Hindus and Muslims; the July Esala festival is electrifying.", "Kataragama temple"),
        _att("Tissa Wewa", CULT, 0, list(range(1, 13)), 6.6, "Ancient irrigation tank near Tissamaharama lined with palmyras — sunrise paddies and pelicans.", "Tissa Wewa"),
        _att("Mulkirigala Rock Temple", RELI, 500, list(range(1, 13)), 6.8, "Cave temples on a 200-metre rock with reclining Buddhas and 18th-century murals; views to the south coast.", "Mulkirigala Raja Maha Vihara"),
        _att("Hambantota Salt Pans", CULT, 0, [2, 3, 4, 5], 6.0, "Vast geometric salt pans on the south-east coast — flamingos and kite-fliers in season.", "Hambantota Salt Lake"),
        _att("Rekawa Turtle Beach", WILD, 1500, list(range(1, 13)), 7.2, "Most consistent green-turtle nesting beach on the island; nightly guided walks year-round.", "Rekawa Beach"),
    ],
    "Jaffna": [
        _att("Nallur Kandaswamy Kovil", RELI, 0, [8, 9], 8.6, "Vast saffron Hindu temple at the heart of Jaffna; 25-day August festival climaxing in chariot processions.", "Nallur Kandaswamy temple"),
        _att("Jaffna Fort", CULT, 0, list(range(1, 13)), 7.6, "17th-century Dutch fort by Jaffna lagoon, with churches, ramparts and a moat.", "Jaffna Fort"),
        _att("Casuarina Beach", BEAC, 0, [5, 6, 7, 8, 9], 7.4, "Shallow turquoise water on Karainagar island, a 45-minute drive from Jaffna town.", "Casuarina Beach"),
        _att("Delft Island", CULT, 0, [5, 6, 7, 8, 9], 7.2, "Coral-walled island reached by ferry — wild ponies, baobabs and a Dutch bathhouse.", "Neduntheevu"),
        _att("Keerimalai Springs", RELI, 0, list(range(1, 13)), 7.0, "Mineral spring pools by the sea, sacred to Hindus and a popular bathing spot.", "Keerimalai"),
        _att("Jaffna Public Library", CULT, 0, list(range(1, 13)), 6.6, "Mughal-style library — burned in 1981, painstakingly rebuilt as a symbol of Tamil resilience.", "Jaffna Public Library"),
        _att("Point Pedro", CULT, 0, [5, 6, 7, 8, 9], 6.4, "Sri Lanka's northernmost tip; a quiet fishing town with a working lighthouse.", "Point Pedro"),
    ],
    "Kilinochchi": [
        _att("Iranamadu Tank", WILD, 0, [5, 6, 7, 8, 9], 6.4, "Vast irrigation reservoir with birding hides and fishermen's catamarans.", "Iranamadu Tank"),
        _att("Kandasamy Kovil, Kilinochchi", RELI, 0, list(range(1, 13)), 6.0, "Lively Murugan temple at the centre of town; deeply meaningful to the local Tamil community.", "Kilinochchi"),
        _att("Elephant Pass Memorial", CULT, 0, list(range(1, 13)), 6.2, "Small but moving war memorial on the causeway connecting Jaffna peninsula to the mainland.", "Elephant Pass"),
        _att("Akkarayan Tank", WILD, 0, [5, 6, 7, 8, 9], 5.8, "Quiet tank on the road to Mullaitivu — kingfishers, lily blooms and palmyra forest.", "Kilinochchi District"),
        _att("Muhamalai Sculpture Park", CULT, 0, list(range(1, 13)), 5.6, "Open-air installation along the A9 road commemorating peace; metalwork by Tamil artists.", "Kilinochchi District"),
    ],
    "Mannar": [
        _att("Adam's Bridge (Rama Setu)", CULT, 0, [5, 6, 7, 8, 9], 7.4, "Chain of limestone shoals stretching towards India — myth says Rama crossed it; today an ecotourism boat trip.", "Adam's Bridge"),
        _att("Mannar Baobabs", CULT, 0, list(range(1, 13)), 7.0, "Giant African baobab trees brought by Arab traders 700+ years ago — the oldest is 1,500 years old.", "Adansonia digitata"),
        _att("Talaimannar Lighthouse", CULT, 0, [5, 6, 7, 8, 9], 6.6, "Whitewashed coastal beacon at the start of the bridge to India; sunset gold.", "Talaimannar"),
        _att("Mannar Fort", CULT, 0, list(range(1, 13)), 6.4, "Square Portuguese fort rebuilt by the Dutch on Mannar Island — coastline cannons and a chapel ruin.", "Mannar Fort"),
        _att("Madhu Church", RELI, 0, [7, 8], 7.0, "Pilgrimage shrine to Our Lady of Madhu — Sri Lanka's most important Catholic site, 400 years old.", "Madhu Church"),
        _att("Vankalai Bird Sanctuary", WILD, 0, [11, 12, 1, 2, 3], 6.6, "Migratory hotspot — flamingos, painted storks and waders winter on its lagoons.", "Vankalai Sanctuary"),
    ],
    "Vavuniya": [
        _att("Madukanda Vihara", RELI, 0, list(range(1, 13)), 6.4, "Believed to be where the Sacred Tooth Relic first stopped on its way to Anuradhapura in 371 AD.", "Madukanda Vihara"),
        _att("Vavuniya Tank", WILD, 0, list(range(1, 13)), 6.0, "Ancient irrigation reservoir in the heart of town; pelicans and morning mist.", "Vavuniya"),
        _att("Kurumankadu Forest Park", WILD, 0, [5, 6, 7, 8, 9], 5.8, "Quiet dry-zone forest with sambar and peacocks; a peaceful picnic stop.", "Vavuniya"),
        _att("Vavuniya Archaeological Museum", CULT, 200, list(range(1, 13)), 5.8, "Compact museum with statues from Anuradhapura-period sites in the Vanni.", "Vavuniya"),
        _att("Pavatkulam Forest Reserve", WILD, 0, [5, 6, 7, 8, 9], 5.6, "Tank-and-forest reserve on the Vavuniya-Mannar road; elephants pass through.", "Vavuniya"),
    ],
    "Mullaitivu": [
        _att("Nayaru Lagoon Beach", BEAC, 0, [5, 6, 7, 8, 9], 6.8, "Empty crescent of white sand where a lagoon meets the sea; one of Sri Lanka's wildest beaches.", "Mullaitivu District"),
        _att("Nanthikadal Lagoon", WILD, 0, [5, 6, 7, 8, 9], 6.6, "Long brackish lagoon ringed by palmyra; shallow water and a haunting recent history.", "Nanthikadal"),
        _att("Mullaitivu Beach", BEAC, 0, [5, 6, 7, 8, 9], 6.4, "Wide quiet beach lined with fishing boats and Indian almond trees.", "Mullaitivu"),
        _att("Kokilai Bird Sanctuary", WILD, 0, [11, 12, 1, 2, 3], 6.4, "Coastal lagoon and mangroves hosting flamingos, herons and storks.", "Kokilai Lagoon"),
        _att("Vattappalai Kannaki Amman Kovil", RELI, 0, list(range(1, 13)), 6.0, "Ancient seaside Hindu temple with an annual chariot festival drawing pilgrims from across the north.", "Mullaitivu"),
    ],
    "Batticaloa": [
        _att("Pasikudah Beach", BEAC, 0, [4, 5, 6, 7, 8, 9], 8.4, "World-famous shallow reef bay — wade out 100 m and the water still only reaches your waist.", "Pasikudah"),
        _att("Kallady Bridge", CULT, 0, list(range(1, 13)), 6.8, "Iron-girder bridge over the lagoon, famous for the 'singing fish' you can hear at full moon.", "Kallady Bridge"),
        _att("Batticaloa Dutch Fort", CULT, 0, list(range(1, 13)), 6.6, "Compact 1628 fort guarding the lagoon, with original Dutch coats of arms above the gate.", "Batticaloa Fort"),
        _att("Kallady Beach", BEAC, 0, [4, 5, 6, 7, 8, 9], 7.4, "Long sandy stretch lined with fishing villages and tamarind trees, near the lagoon mouth.", "Kallady"),
        _att("Mandoor Kandaswamy Kovil", RELI, 0, list(range(1, 13)), 6.4, "8th-century Hindu temple with a beautiful chariot procession at the annual festival.", "Mandoor Kandaswamy Temple"),
        _att("Lighthouse Point", CULT, 0, list(range(1, 13)), 6.6, "Restored 1913 lighthouse at the lagoon mouth, with views over fishing canoes and the sea.", "Batticaloa Lighthouse"),
    ],
    "Ampara": [
        _att("Arugam Bay", BEAC, 0, [5, 6, 7, 8, 9], 9.0, "World-class right-hand point break — the heart of Sri Lanka's surf scene every May to October.", "Arugam Bay"),
        _att("Whiskey Point", BEAC, 0, [5, 6, 7, 8, 9], 7.8, "Mellow beach break 10 minutes north of Arugam Bay — the local longboard hangout.", "Arugam Bay"),
        _att("Lahugala-Kitulana National Park", WILD, 4500, [5, 6, 7, 8, 9], 7.0, "Small park where elephants gather to feed on tank-grass; quieter than Yala.", "Lahugala-Kitulana National Park"),
        _att("Magul Maha Viharaya", RELI, 0, list(range(1, 13)), 6.6, "2nd-century BC ruins where King Kavantissa is said to have married Queen Viharamahadevi.", "Magul Maha Viharaya"),
        _att("Kudumbigala Forest Monastery", RELI, 500, list(range(1, 13)), 7.2, "Forest monastery on a granite outcrop with cave hermitages and a hilltop dagoba; meditative views over Yala.", "Kudumbigala Forest Monastery"),
        _att("Pottuvil Lagoon", WILD, 1500, [5, 6, 7, 8, 9], 7.0, "Mangrove paddle near Arugam Bay — crocodiles, painted storks and wild elephants on the banks.", "Pottuvil"),
    ],
    "Trincomalee": [
        _att("Koneswaram Temple", RELI, 0, list(range(1, 13)), 8.4, "Cliff-top Hindu temple at Swami Rock, one of the five sacred Pancha Ishwarams of Shiva in Sri Lanka.", "Koneswaram Temple"),
        _att("Nilaveli Beach", BEAC, 0, [4, 5, 6, 7, 8, 9], 8.6, "Six kilometres of white sand and warm shallow water; jumping-off point for Pigeon Island.", "Nilaveli"),
        _att("Pigeon Island National Park", WILD, 5500, [4, 5, 6, 7, 8, 9], 8.2, "Small island with vibrant coral reefs and reef sharks 15 minutes by boat from Nilaveli.", "Pigeon Island National Park"),
        _att("Uppuveli Beach", BEAC, 0, [4, 5, 6, 7, 8, 9], 7.6, "Quieter cousin of Nilaveli with simple beach guesthouses and fresh seafood.", "Uppuveli"),
        _att("Trincomalee Fort (Fort Frederick)", CULT, 0, list(range(1, 13)), 7.0, "Portuguese-built fort still partly garrisoned, with herds of friendly spotted deer roaming the ramparts.", "Fort Frederick, Trincomalee"),
        _att("Marble Beach", BEAC, 0, [4, 5, 6, 7, 8, 9], 7.0, "Tranquil military-administered cove with calm water, picnic shelters and snorkelling.", "Marble Beach (Sri Lanka)"),
        _att("Kanniya Hot Springs", CULT, 200, list(range(1, 13)), 6.4, "Seven enclosed hot wells beside an ancient temple just outside Trincomalee.", "Kanniya Hot Springs"),
    ],
    "Kurunegala": [
        _att("Yapahuwa Rock Fortress", CULT, 1500, list(range(1, 13)), 7.6, "13th-century rock citadel with an ornamental staircase echoing Sigiriya; once held the Tooth Relic.", "Yapahuwa"),
        _att("Athugala Rock", ADVE, 0, list(range(1, 13)), 6.6, "'Elephant Rock' towering over Kurunegala town — a 30-minute climb to a giant white Buddha at the summit.", "Kurunegala"),
        _att("Panduwasnuwara Royal Citadel", CULT, 500, list(range(1, 13)), 6.2, "12th-century capital with palace ruins, a temple of the tooth and a royal swimming pool.", "Panduwasnuwara"),
        _att("Ridi Vihara", RELI, 250, list(range(1, 13)), 6.6, "Silver-mine cave temple with intricate Kandyan-period murals.", "Ridi Vihara"),
        _att("Arankele Forest Monastery", RELI, 200, list(range(1, 13)), 6.4, "Tranquil 6th-century forest monastery on a wooded hillside; ruined meditation paths and ponds.", "Arankele"),
        _att("Pahala Maharachchimulla Coconut Triangle", CULT, 0, list(range(1, 13)), 5.8, "Heart of Sri Lanka's coconut belt — endless palm avenues and small cottage industries.", "Coconut Triangle"),
    ],
    "Puttalam": [
        _att("Wilpattu National Park", WILD, 5500, [2, 3, 4, 5, 6, 7], 8.8, "Sri Lanka's largest national park — leopards, sloth bears and over 50 willu (rain-fed lakes).", "Wilpattu National Park"),
        _att("Kalpitiya Lagoon Kitesurfing", ADVE, 0, [5, 6, 7, 8, 9], 8.0, "Flat-water kitesurfing paradise from May to September; beginners and pros alike.", "Kalpitiya"),
        _att("Dolphin Watching, Kalpitiya", WILD, 6000, [11, 12, 1, 2, 3], 7.6, "Pods of 1,000+ spinner dolphins are common just offshore; sperm whales sometimes follow.", "Kalpitiya"),
        _att("Munneswaram Temple", RELI, 0, [8, 9], 7.0, "One of the five Pancha Ishwarams; the August festival features fire-walking devotees.", "Munneswaram temple"),
        _att("Anawilundawa Wetland Sanctuary", WILD, 600, [11, 12, 1, 2, 3], 6.6, "Ramsar-listed mosaic of tanks, mangroves and rice paddies; 150+ bird species.", "Anawilundawa Sanctuary"),
        _att("Kudiramalai Point", CULT, 0, [5, 6, 7, 8, 9], 6.6, "Red-cliff promontory with a cinematic baobab and crystal water; remote and lightly visited.", "Kudremalai"),
    ],
    "Anuradhapura": [
        _att("Sri Maha Bodhi", RELI, 0, list(range(1, 13)), 9.0, "The world's oldest documented planted tree, grown from a cutting of the Bodhi tree under which the Buddha attained enlightenment.", "Sri Maha Bodhi"),
        _att("Ruwanwelisaya", RELI, 0, list(range(1, 13)), 8.6, "Towering white stupa built by King Dutugamunu in the 2nd century BC — pilgrimage site at full moon.", "Ruwanwelisaya"),
        _att("Jetavanaramaya", RELI, 1500, list(range(1, 13)), 8.0, "Once the world's third-tallest structure (122 m); brick stupa from the 3rd century AD.", "Jetavanaramaya"),
        _att("Abhayagiri Monastery", RELI, 1500, list(range(1, 13)), 7.6, "Sprawling ancient monastery with the Samadhi Buddha statue and elaborate moonstones.", "Abhayagiri vihāra"),
        _att("Isurumuniya Temple", RELI, 250, list(range(1, 13)), 7.2, "Rock-cut temple famous for the carved 'Lovers' relief; pleasant pond and steps cut from the stone.", "Isurumuniya"),
        _att("Mihintale", RELI, 1000, [6, 7, 8, 9], 8.0, "Cradle of Sri Lankan Buddhism — climb 1,840 steps to where King Devanampiya Tissa met Mahinda in 247 BC.", "Mihintale"),
        _att("Ritigala Forest Monastery", RELI, 1500, [5, 6, 7, 8, 9], 7.4, "Mountain monastery in dense jungle with paved meditation paths and stone double-platforms.", "Ritigala"),
        _att("Aukana Buddha Statue", RELI, 500, list(range(1, 13)), 6.8, "12-metre standing Buddha carved from a single granite outcrop in the 5th century.", "Avukana Buddha statue"),
        _att("Twin Ponds (Kuttam Pokuna)", CULT, 0, list(range(1, 13)), 7.0, "Pair of 8th-century rectangular bathing pools in granite — engineering marvel and a serene picnic spot.", "Kuttam Pokuna"),
    ],
    "Polonnaruwa": [
        _att("Gal Vihara", RELI, 0, list(range(1, 13)), 9.2, "Four colossal Buddhas carved from a single granite cliff in the 12th century — the artistic high point of medieval Sri Lanka.", "Gal Vihara"),
        _att("Royal Palace of King Parakramabahu", CULT, 0, list(range(1, 13)), 7.4, "Originally seven-storey palace with three-metre-thick walls; only the brick shell now remains.", "Polonnaruwa"),
        _att("Rankoth Vehera", RELI, 0, list(range(1, 13)), 7.2, "Largest stupa in Polonnaruwa, modelled on Anuradhapura's Ruwanwelisaya.", "Rankoth Vehera"),
        _att("Vatadage", CULT, 0, list(range(1, 13)), 8.0, "Circular relic house with concentric rings of pillars, four entrance Buddhas and exquisite stonework.", "Polonnaruwa Vatadage"),
        _att("Lankathilaka Image House", RELI, 0, list(range(1, 13)), 7.0, "Roofless brick image house with an enormous standing Buddha rising 17 metres into the sky.", "Lankatilaka, Polonnaruwa"),
        _att("Parakrama Samudra", CULT, 0, list(range(1, 13)), 7.4, "5,600-hectare 12th-century reservoir with a sunset cycle path along the bund — pelicans glide on still water.", "Parakrama Samudra"),
        _att("Minneriya National Park", WILD, 5500, [7, 8, 9, 10], 8.6, "Stage of 'The Gathering' — up to 300 wild elephants assemble around the tank in dry season.", "Minneriya National Park"),
        _att("Medirigiriya Vatadage", RELI, 500, list(range(1, 13)), 6.4, "Hidden 8th-century circular shrine on a forested hill, three concentric stone columns surrounding the dagoba.", "Medirigiriya Vatadage"),
    ],
    "Badulla": [
        _att("Ella Rock", ADVE, 0, [1, 2, 3, 7, 8, 9], 9.0, "4-hour return hike with sweeping views of Ella Gap; start at sunrise to beat the heat.", "Ella, Sri Lanka"),
        _att("Nine Arches Bridge", CULT, 0, list(range(1, 13)), 9.4, "Iconic 1921 colonial-era stone railway bridge; train passes around 06:30, 09:30, 11:00 and 15:00.", "Nine Arches Bridge"),
        _att("Little Adam's Peak", ADVE, 0, [1, 2, 3, 7, 8, 9], 8.4, "Easy 45-minute climb with classic Hill Country views; great for sunrise or sunset.", "Little Adam's Peak"),
        _att("Ravana Falls", ADVE, 200, [10, 11, 12, 1, 2], 7.8, "25-metre roadside waterfall named after the Ramayana king who allegedly hid Sita in nearby caves.", "Ravana Falls"),
        _att("Demodara Loop", CULT, 0, list(range(1, 13)), 6.8, "Engineering marvel where the railway loops over itself to gain elevation.", "Demodara"),
        _att("Lipton's Seat", CULT, 0, [1, 2, 3, 7, 8], 7.4, "Hilltop viewpoint where Sir Thomas Lipton surveyed his tea empire; reach it before 09:00 for clear views.", "Lipton's Seat"),
        _att("Dunhinda Falls", ADVE, 100, [10, 11, 12, 1, 2], 7.0, "63-metre fall reached via a one-kilometre forest path from Badulla.", "Dunhinda Falls"),
        _att("Diyaluma Falls", ADVE, 0, [10, 11, 12, 1, 2], 7.6, "220-metre cascade — the country's second-tallest — with infinity-pool plunge pools at the top.", "Diyaluma Falls"),
        _att("Bogoda Wooden Bridge", CULT, 0, list(range(1, 13)), 6.2, "16th-century wooden bridge with a shingled roof; one of the oldest of its kind in Asia.", "Bogoda Wooden Bridge"),
        _att("Muthiyangana Raja Maha Vihara", RELI, 0, list(range(1, 13)), 6.4, "Ancient temple in central Badulla, said to mark a visit by the Buddha himself.", "Muthiyangana Raja Maha Vihara"),
    ],
    "Moneragala": [
        _att("Maligawila Buddha Statue", RELI, 0, list(range(1, 13)), 7.4, "11.5-metre standing Buddha carved from a single piece of limestone in the 7th century — toppled, then re-erected in 1991.", "Maligawila"),
        _att("Yudaganawa Stupa", RELI, 200, list(range(1, 13)), 6.8, "Massive 2nd-century BC stupa marking the battle between brothers Dutugamunu and Saddhatissa.", "Yudaganawa"),
        _att("Buduruwagala", RELI, 500, list(range(1, 13)), 7.6, "Seven 9th-century rock-cut figures including a 51-metre standing Buddha — Sri Lanka's tallest carving.", "Buduruwagala"),
        _att("Dombagahawela Goda Senanayake Tank", WILD, 0, [5, 6, 7, 8, 9], 6.0, "Quiet birdwatching tank in dry-zone hill country.", "Moneragala District"),
        _att("Yala East / Kumana", WILD, 5000, [4, 5, 6, 7, 8, 9], 7.6, "Bird-rich, leopard-rich eastern wilderness adjoining Yala — far less crowded than Block 1.", "Kumana National Park"),
        _att("Galge Forest Monastery", RELI, 0, list(range(1, 13)), 6.0, "Forgotten 9th-century forest monastery with a beautifully sculpted moonstone.", "Moneragala District"),
    ],
    "Ratnapura": [
        _att("Sinharaja Forest Reserve", WILD, 1500, [1, 2, 3, 7, 8, 9], 8.6, "UNESCO-listed virgin lowland rainforest; biodiversity hotspot of the Indian Ocean.", "Sinharaja Forest Reserve"),
        _att("Adam's Peak (Sri Pada)", ADVE, 0, [12, 1, 2, 3, 4], 9.0, "2,243-metre conical mountain climbed in pre-dawn pilgrimage; reveals a perfect triangular shadow at sunrise.", "Adam's Peak"),
        _att("Bopath Ella Falls", ADVE, 0, [1, 2, 3, 7, 8], 7.0, "30-metre falls shaped like a Bo leaf; popular swimming pool at the base.", "Bopath Falls"),
        _att("Ratnapura Gem Museum", CULT, 1000, list(range(1, 13)), 6.4, "Comprehensive collection of Sri Lanka's gem heritage — sapphires, cat's eyes and moonstones.", "Ratnapura"),
        _att("Pothgul Vihara, Hanwella", RELI, 0, list(range(1, 13)), 6.0, "Old library temple with palm-leaf manuscripts and a quiet hilltop dagoba.", "Pothgul Vihara, Polonnaruwa"),
        _att("Udawalawe National Park", WILD, 5500, [5, 6, 7, 8, 9], 8.4, "Best place in Sri Lanka to reliably see wild elephants, plus the adjacent elephant transit home.", "Udawalawe National Park"),
        _att("Saman Devalaya", RELI, 0, list(range(1, 13)), 6.4, "Hilltop temple of god Saman, guardian of Adam's Peak; striking river-side setting.", "Saman Devalaya"),
    ],
    "Kegalle": [
        _att("Pinnawala Elephant Orphanage", WILD, 3000, list(range(1, 13)), 8.2, "World-renowned sanctuary where rescued elephants bottle-feed and bathe in the Maha Oya river twice a day.", "Pinnawala Elephant Orphanage"),
        _att("Bible Rock (Bathalegala)", ADVE, 0, [1, 2, 3, 7, 8], 7.4, "Flat-topped peak resembling an open book; 4-hour return hike with panoramic views.", "Bathalegala"),
        _att("Utuwankanda (Saradiel's Rock)", ADVE, 0, list(range(1, 13)), 6.4, "Hideout of Sri Lanka's 'Robin Hood' bandit Utuwankanda Sura Saradiel — short scramble to the summit.", "Utuwankanda"),
        _att("Beli Lena Cave", CULT, 200, [1, 2, 3, 7, 8], 6.6, "Pre-historic cave shelter where 30,000-year-old human remains were unearthed.", "Belilena"),
        _att("Mahasaman Devalaya, Ratnapura Road", RELI, 0, [4, 8], 6.6, "Old-world devalaya complex hosting a colourful July-August perahera.", "Mahasaman Devale"),
        _att("Dehigaha Ela", WILD, 0, [1, 2, 3, 7, 8], 6.0, "Quiet rainforest stream with rope bridges and freshwater pools, near Kitulgala.", "Kitulgala"),
        _att("Kitulgala Whitewater Rafting", ADVE, 4000, [5, 6, 7, 8, 9, 10], 7.8, "Class 2-3 rapids on the Kelani River; the bridge from 'The Bridge on the River Kwai' lies just upstream.", "Kitulgala"),
    ],
}


# ─────────────────────────── Command ───────────────────────────────────
class Command(BaseCommand):
    help = (
        "Seed all 25 Sri Lankan districts and curated attractions. "
        "Idempotent unless --flush is supplied."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete all existing districts/attractions/media before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts["flush"]:
            MediaAsset.objects.all().delete()
            Attraction.objects.all().delete()
            District.objects.all().delete()
            self.stdout.write(self.style.WARNING("Flushed media + attractions + districts."))

        district_lookup: dict[str, District] = {}
        for d in DISTRICTS:
            slug = slugify(d["name"])
            obj, created = District.objects.update_or_create(
                name=d["name"],
                defaults={
                    "slug": slug,
                    "province": d["province"],
                    "lat": d["lat"],
                    "lng": d["lng"],
                    "climate_zone": d["climate"],
                    "peak_months": d["peak"],
                    "youtube_video_ids": d.get("yt") or [],
                    "description": d.get("desc")
                    or f"{d['name']} is one of the {d['province']} Province districts of Sri Lanka.",
                },
            )
            district_lookup[d["name"]] = obj
            self.stdout.write(
                ("+ " if created else "  ") + f"district: {d['name']} ({d['province']})"
            )

        attraction_count = 0
        for district_name, attractions in ATTRACTIONS.items():
            district = district_lookup[district_name]
            for a in attractions:
                slug = slugify(f"{a['name']}-{district_name}")
                _, created = Attraction.objects.update_or_create(
                    slug=slug,
                    defaults={
                        "district": district,
                        "name": a["name"],
                        "category": a["category"],
                        "description": a["desc"],
                        "address": district_name,
                        "lat": district.lat,
                        "lng": district.lng,
                        "entry_fee_lkr": a["fee"],
                        "best_season": a["season"],
                        "crowd_index": min(10, max(1, int(a["trend"]))),
                        "trend_score": a["trend"],
                        "wikipedia_title": a.get("wiki", a["name"]),
                        "youtube_video_id": a.get("yt", ""),
                    },
                )
                if created:
                    attraction_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed complete: {District.objects.count()} districts, "
                f"{Attraction.objects.count()} attractions "
                f"({attraction_count} new this run)."
            )
        )
