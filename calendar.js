/* Throttle & Rust — "On the calendar" rail.
 *
 * The homepage shows the FIRST entry whose date has not passed yet, so this
 * advances itself. No weekly edit required. When the list runs out, the
 * offSeason entry below is shown instead.
 *
 * To edit: change the copy, add an entry, or delete one. Keep the list in
 * date order. Dates are YYYY-MM-DD and an entry stays up through the end of
 * its own day.
 *
 * Voice rules still apply here: no exclamation points, no em-dashes, no
 * sentence opening with "I", no call to action, no naming drivers or results.
 * The only racing stat the property owns is 4th in points at Hickory in '89.
 */

window.TR_CALENDAR = [

  {
    date: "2026-08-29",
    kicker: "Daytona. August 29.",
    body: "Saturday night at Daytona closes out the regular season, which means the whole year gets decided by a place where the driving matters least. Ricky has opinions about that and does not keep them quiet. The pot goes on the burner either way."
  },

  {
    date: "2026-09-06",
    kicker: "Darlington. Labor Day.",
    body: "The Southern 500 runs Sunday evening on a track shaped wrong on purpose, and the cars come out in paint from thirty and forty years back. Ricky watches his own decade go by in somebody else's colors. Sarah wears the shirt, which is not a throwback because it never left."
  },

  {
    date: "2026-09-13",
    kicker: "Madison, Illinois. September 13.",
    body: "A mile and a quarter across the river from St. Louis, flat and worn and nobody's crown jewel. Ricky likes the ones with no ceremony attached. Second week of the chase and the table is already back out of the rafters."
  },

  {
    date: "2026-09-19",
    kicker: "Bristol. September 19.",
    body: "Cup cars run the night race at Bristol on the nineteenth, half a mile of concrete banked up like a coliseum. Ricky ran bullrings a fraction the size of it, and he'll tell you Bristol is the last big track that still races like the little ones did. The pot goes on the burner either way."
  },

  {
    date: "2026-09-27",
    kicker: "Kansas. September 27.",
    body: "Four turns, a mile and a half, built in a field in 2001. Ella Mae calls it the one where they all look the same, and she is not entirely wrong. She brings a book regardless."
  },

  {
    date: "2026-10-04",
    kicker: "Las Vegas. October 4.",
    body: "A five-thirty green flag out west means the race ends after dark here, which is the part Ricky likes. Nothing about the place resembles anywhere he ever ran. He watches all of it anyway."
  },

  {
    date: "2026-10-11",
    kicker: "Charlotte. October 11.",
    body: "An hour down the road, which is close enough that the light over the ridge and the noise on the radio belong to the same evening. Ricky worked a dealership counter through the years the sport moved to that town. He has never once called it a coincidence."
  },

  {
    date: "2026-10-18",
    kicker: "Phoenix. October 18.",
    body: "The ridges are turning by now and the racing is out in the desert, which is a strange pair of things to hold in one afternoon. Leaf color peaks somewhere in this week most years. The porch gets used more than the television does."
  },

  {
    date: "2026-10-25",
    kicker: "Talladega. October 25.",
    body: "Two and a half miles of Alabama where forty cars run in a knot and nobody is really steering. Ricky calls it a lottery with a fuel bill. Ella Mae leaves the room for the last ten laps and has for forty years."
  },

  {
    date: "2026-11-01",
    kicker: "Martinsville. November 1.",
    body: "Half a mile of flat asphalt and concrete corners two hours up the road from Wilkesboro, and the oldest thing still on the schedule. Ricky ran tracks built on the same idea and will tell you the idea was correct. Ella Mae comes for the hot dogs and does not pretend otherwise."
  },

  {
    date: "2026-11-08",
    kicker: "Homestead. November 8.",
    body: "Last one of the year, and then the season is a thing that happened. The pot comes off the burner until February. The truck goes back up on stands the week after."
  },

  {
    date: "2026-11-26",
    kicker: "Thanksgiving.",
    body: "The table comes down out of the rafters for the last time this year and does not go back for a while. Ricky and Ella Mae drive over Wednesday. Nothing is on and nobody minds."
  },

  {
    date: "2026-12-31",
    kicker: "Build season.",
    body: "Cold garage, warm tungsten, the '54 up on stands with more of it apart than together. This is the stretch where the truck actually gets worked on instead of talked about. February is a long way off and that is the point."
  }

];

/* Shown once every dated entry above has passed. Keep it evergreen. */
window.TR_CALENDAR_OFFSEASON = {
  kicker: "Build season.",
  body: "Cold garage, warm tungsten, the '54 up on stands with more of it apart than together. This is the stretch where the truck actually gets worked on instead of talked about."
};
