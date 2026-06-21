/**
 * One local public asset per attraction slug — no keyword/district fallbacks,
 * so the same file never fills unrelated cards.
 */

/** Safe URL for files in `public/` (handles spaces and special chars). */
export function localPublic(fileName: string): string {
  return `/${fileName.split("/").map(encodeURIComponent).join("/")}`;
}

/** Attraction slug → dedicated image (1:1, no reuse). */
const SLUG_TO_IMAGE: Record<string, string> = {
  "abhayagiri-monastery-anuradhapura": localPublic("abhayagiri-vihara.webp"),
  "adams-bridge-rama-setu-mannar": localPublic("rama-setu-adam-bridge.webp"),
  "adams-peak-sri-pada-ratnapura": localPublic("sri-pada.webp"),
  "anawilundawa-wetland-sanctuary-puttalam": localPublic("Anawilundawa.webp"),
  "arugam-bay-ampara": localPublic("Arugam-Bay.webp"),
  "athugala-rock-kurunegala": localPublic("athugala.webp"),
  "bahirawakanda-vihara-buddha-statue-kandy": localPublic("bahirawakanda-vihara.webp"),
  "bible-rock-bathalegala-kegalle": localPublic("bathalegala-mountain.webp"),
  "bopath-ella-falls-ratnapura": localPublic("bopath ella.webp"),
  "brief-garden-kalutara": localPublic("brief-garden-kalutara.webp"),
  "buduruwagala-moneragala": localPublic("buduruwagala.webp"),
  "diyaluma-falls-badulla": localPublic("diyaluma-waterfall.webp"),
  "dolphin-watching-kalpitiya-puttalam": localPublic("Kalpitiya-dolphin.webp"),
  "dunhinda-falls-badulla": localPublic("dunhinda-falls.webp"),
  "dutch-hospital-shopping-precinct-colombo": localPublic(
    "Dutch-Hospital-Shopping.webp"
  ),
  "ella-rock-badulla": localPublic("ella-rock.webp"),
  "esala-perahera-procession-route-kandy": localPublic(
    "Kandy-Esala-Perahera.webp"
  ),
  "gal-vihara-polonnaruwa": localPublic("polonnaruwa-gal-vihara.webp"),
  "isurumuniya-temple-anuradhapura": localPublic("Isurumuniya-Temple.webp"),
  "jetavanaramaya-anuradhapura": localPublic("jetavanaramaya.webp"),
  "jungle-beach-galle": localPublic("Jungle_Beach.webp"),
  "kallady-beach-batticaloa": localPublic("kallady-beach.webp"),
  "kalpitiya-lagoon-kitesurfing-puttalam": localPublic("wingfoiling-kalpitiya.webp"),
  "kitulgala-whitewater-rafting-kegalle": localPublic("kitulgala-whitewater.webp"),
  "koneswaram-temple-trincomalee": localPublic("Koneswaram_temple.webp"),
  "kosgoda-beach-galle": localPublic("kosgoda beach.webp"),
  "kudumbigala-forest-monastery-ampara": localPublic("kudumbigala.webp"),
  "lahugala-kitulana-national-park-ampara": localPublic(
    "Lahugala-Kitulana-National-Park.webp"
  ),
  "liptons-seat-badulla": localPublic("lipton-seat.webp"),
  "little-adams-peak-badulla": localPublic("little-adams-peak.webp"),
  "maligawila-buddha-statue-moneragala": localPublic("Maligawila.webp"),
  "marble-beach-trincomalee": localPublic("Marble-Beach.webp"),
  "mihintale-anuradhapura": localPublic("Visiter-Mihintale.webp"),
  "minneriya-national-park-polonnaruwa": localPublic("Minneriya-National.webp"),
  "mirissa-whale-watching-matara": localPublic("whale-watching-mirissa.webp"),
  "mullaitivu-beach-mullaitivu": localPublic("mullativu-beach.webp"),
  "nanthikadal-lagoon-mullaitivu": localPublic("Nanthikadal.webp"),
  "nayaru-lagoon-beach-mullaitivu": localPublic("nayaru-beach.webp"),
  "nilaveli-beach-trincomalee": localPublic("nilaveli.webp"),
  "nine-arches-bridge-badulla": localPublic("9-arch-bridge.webp"),
  "parakrama-samudra-polonnaruwa": localPublic("Parakrama Samudra.webp"),
  "pasikudah-beach-batticaloa": localPublic("pasikuda-beach.webp"),
  "pedro-tea-estate-nuwara-eliya": localPublic("pedro-tea.webp"),
  "pettah-market-colombo": localPublic("pettah-market.webp"),
  "pidurangala-rock-matale": localPublic("pidurangala-rock.webp"),
  "pigeon-island-national-park-trincomalee": localPublic(
    "pigeon-island-national-park.webp"
  ),
  "pinnawala-elephant-orphanage-kegalle": localPublic("pinnawala.webp"),
  "polhena-reef-matara": localPublic("polhena-beach.webp"),
  "pottuvil-lagoon-ampara": localPublic("lagoon-pottuvil.webp"),
  "ravana-falls-badulla": localPublic("ravana-falls.webp"),
  "rekawa-turtle-beach-hambantota": localPublic("Sea-turtles-in-rekawa-beach.webp"),
  "ritigala-forest-monastery-anuradhapura": localPublic("ritigala.webp"),
  "riverston-mini-worlds-end-matale": localPublic("Riverston-mini-Worlds-End.webp"),
  "royal-palace-of-king-parakramabahu-polonnaruwa": localPublic(
    "Royal Palace of King Parakramabahu.webp"
  ),
  "ruwanwelisaya-anuradhapura": localPublic("ruwanwelisaya.webp"),
  "sigiriya-rock-fortress-matale": localPublic("hero-sigiriya.webp"),
  "single-tree-hill-nuwara-eliya": localPublic("nuwara-eliya-single-tree-hill.webp"),
  "sinharaja-forest-reserve-ratnapura": localPublic("sinharaja.webp"),
  "sri-maha-bodhi-anuradhapura": localPublic("Sri-Maha-Bodhi.webp"),
  "udawalawe-national-park-ratnapura": localPublic("udawalawe.webp"),
  "uppuveli-beach-trincomalee": localPublic("Uppuveli-Beach.webp"),
  "utuwankanda-saradiels-rock-kegalle": localPublic("Utuwankanda-Saradiel Rock.webp"),
  "vatadage-polonnaruwa": localPublic("pollonnaruwa_watagade.webp"),
  "whiskey-point-ampara": localPublic("wiskey.webp"),
  "wilpattu-national-park-puttalam": localPublic("Wilpattu-National-Park.webp"),
  "yala-east-kumana-moneragala": localPublic("yala.webp"),
  "yala-national-park-hambantota": localPublic("yala.webp"),
  "yapahuwa-rock-fortress-kurunegala": localPublic("Yapahuwa-Rock-Fortress.webp"),
  // ── Real Wikimedia/Commons photography sourced for previously image-less
  //    attractions (filenames are <slug>.webp, 1:1 with the attraction). ──
  "aukana-buddha-statue-anuradhapura": localPublic("aukana-buddha-statue-anuradhapura.webp"),
  "batticaloa-dutch-fort-batticaloa": localPublic("batticaloa-dutch-fort-batticaloa.webp"),
  "bogoda-wooden-bridge-badulla": localPublic("bogoda-wooden-bridge-badulla.webp"),
  "dehigaha-ela-kegalle": localPublic("dehigaha-ela-kegalle.webp"),
  "demodara-loop-badulla": localPublic("demodara-loop-badulla.webp"),
  "gregory-lake-nuwara-eliya": localPublic("gregory-lake-nuwara-eliya.webp"),
  "henarathgoda-botanical-gardens-gampaha": localPublic("henarathgoda-botanical-gardens-gampaha.webp"),
  "hiyare-reservoir-rainforest-galle": localPublic("hiyare-reservoir-rainforest-galle.webp"),
  "japanese-peace-pagoda-galle": localPublic("japanese-peace-pagoda-galle.webp"),
  "kallady-bridge-batticaloa": localPublic("kallady-bridge-batticaloa.webp"),
  "kanniya-hot-springs-trincomalee": localPublic("kanniya-hot-springs-trincomalee.webp"),
  "kudiramalai-point-puttalam": localPublic("kudiramalai-point-puttalam.webp"),
  "lankathilaka-image-house-polonnaruwa": localPublic("lankathilaka-image-house-polonnaruwa.webp"),
  "lighthouse-point-batticaloa": localPublic("lighthouse-point-batticaloa.webp"),
  "lovers-leap-waterfall-nuwara-eliya": localPublic("lovers-leap-waterfall-nuwara-eliya.webp"),
  "madhu-church-mannar": localPublic("madhu-church-mannar.webp"),
  "magul-maha-viharaya-ampara": localPublic("magul-maha-viharaya-ampara.webp"),
  "mahasaman-devalaya-ratnapura-road-kegalle": localPublic("mahasaman-devalaya-ratnapura-road-kegalle.webp"),
  "mannar-baobabs-mannar": localPublic("mannar-baobabs-mannar.webp"),
  "mannar-fort-mannar": localPublic("mannar-fort-mannar.webp"),
  "maritime-archaeology-museum-galle": localPublic("maritime-archaeology-museum-galle.webp"),
  "medirigiriya-vatadage-polonnaruwa": localPublic("medirigiriya-vatadage-polonnaruwa.webp"),
  "munneswaram-temple-puttalam": localPublic("munneswaram-temple-puttalam.webp"),
  "muthiyangana-raja-maha-vihara-badulla": localPublic("muthiyangana-raja-maha-vihara-badulla.webp"),
  "muthurajawela-wetland-gampaha": localPublic("muthurajawela-wetland-gampaha.webp"),
  "pahala-maharachchimulla-coconut-triangle-kurunegala": localPublic("pahala-maharachchimulla-coconut-triangle-kurunegala.webp"),
  "panduwasnuwara-royal-citadel-kurunegala": localPublic("panduwasnuwara-royal-citadel-kurunegala.webp"),
  "rankoth-vehera-polonnaruwa": localPublic("rankoth-vehera-polonnaruwa.webp"),
  "ratnapura-gem-museum-ratnapura": localPublic("ratnapura-gem-museum-ratnapura.webp"),
  "richmond-castle-kalutara": localPublic("richmond-castle-kalutara.webp"),
  "ridi-vihara-kurunegala": localPublic("ridi-vihara-kurunegala.webp"),
  "saman-devalaya-ratnapura": localPublic("saman-devalaya-ratnapura.webp"),
  "stilt-fishermen-of-koggala-galle": localPublic("stilt-fishermen-of-koggala-galle.webp"),
  "talaimannar-lighthouse-mannar": localPublic("talaimannar-lighthouse-mannar.webp"),
  "tissa-wewa-hambantota": localPublic("tissa-wewa-hambantota.webp"),
  "trincomalee-fort-fort-frederick-trincomalee": localPublic("trincomalee-fort-fort-frederick-trincomalee.webp"),
  "twin-ponds-kuttam-pokuna-anuradhapura": localPublic("twin-ponds-kuttam-pokuna-anuradhapura.webp"),
  "vattappalai-kannaki-amman-kovil-mullaitivu": localPublic("vattappalai-kannaki-amman-kovil-mullaitivu.webp"),
  "vavuniya-archaeological-museum-vavuniya": localPublic("vavuniya-archaeological-museum-vavuniya.webp"),
  "weherahena-buddhist-temple-matara": localPublic("weherahena-buddhist-temple-matara.webp"),
  "yudaganawa-stupa-moneragala": localPublic("yudaganawa-stupa-moneragala.webp"),
};

export function getLocalImageForSlug(slug: string): string {
  const key = slug.trim().toLowerCase();
  return key ? (SLUG_TO_IMAGE[key] ?? "") : "";
}

export function resolveLocalAttractionImage(hint: { slug?: string }): string {
  return getLocalImageForSlug(hint.slug ?? "");
}
