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
    body: "An hour and a half down the road, which is close enough that the light over the ridge and the noise on the radio belong to the same evening. Ricky worked a dealership counter through the years the sport moved to that town. He has never once called it a coincidence."
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
  },

  /* 2027 runway. The schedule was published August 26, 2026, so the three
     seasonal placeholders that used to sit here have been replaced with real
     dated entries. January stays seasonal because nothing runs in January.
     Dates below are the Cup dates off the released schedule. Keep a few
     entries ahead of today so the calendar page never runs dry. */

  {
    date: "2027-01-17",
    kicker: "Deep winter.",
    body: "Nothing on the schedule and nothing on the radio, which is the only stretch of the year the garage gets somebody's whole attention. The '54 is further apart in January than it is any other month. Ella Mae calls this the quiet part and means it kindly."
  },

  {
    date: "2027-02-13",
    kicker: "Daytona. February 13.",
    body: "The season comes back the way it always does, in Florida, in the cold half of the year. Nothing counts yet, which has never once stopped Ricky from watching the whole thing. The pot comes off the shelf a week early."
  },

  {
    date: "2027-02-21",
    kicker: "The 500. February 21.",
    body: "Five hundred miles to open a year, which is backwards from how every other sport does it. The table comes down out of the rafters for the first time since Thanksgiving. Ella Mae finds something to do in the kitchen for the last twenty laps and hears about all of it from the doorway."
  },

  {
    date: "2027-02-28",
    kicker: "Atlanta. February 28.",
    body: "A mile and a half rebuilt into something that races like a superspeedway, which nobody asked for and most people have since decided they like. Ricky calls it a track that changed its mind. Cold enough here that the fire gets lit before the green flag."
  },

  {
    date: "2027-03-07",
    kicker: "Austin. March 7.",
    body: "A road course in Texas, twenty turns of it, watched with the particular patience of a man who never once turned right on purpose. Sarah likes these better than her father does and says so. The radio stays on regardless."
  },

  {
    date: "2027-03-14",
    kicker: "Phoenix. March 14.",
    body: "Water is up in the creeks by the middle of March and the trout start being worth the walk, which pulls Caleb off the truck for the first Saturday since October. The race runs out in the desert that evening and gets heard more than it gets watched. Nothing about March gets decided."
  },

  {
    date: "2027-03-21",
    kicker: "Las Vegas. March 21.",
    body: "Three time zones west, so the green flag falls after the yard is done and supper is cleared off. Wes turns up somewhere around lap sixty with a guitar he does not play until it is over. The fire gets lit either way."
  },

  {
    date: "2027-04-04",
    kicker: "Darlington. April 4.",
    body: "Egg-shaped, narrow, and older than nearly everything else still on the schedule, which is the entire argument for it. Ricky ran places built on the same stubborn idea at a tenth the size. The mark you leave on the wall there is the only trophy anybody brings up."
  },

  {
    date: "2027-04-11",
    kicker: "Bristol. April 11.",
    body: "Half a mile of concrete banked up like a coliseum, run in daylight this time, which changes the place more than it ought to. The spring one never gets the reputation the August one does. Ricky says the track cannot tell what month it is."
  },

  {
    date: "2027-04-18",
    kicker: "Martinsville. April 18.",
    body: "Flat half-mile up in Virginia, close enough that people from Wilkesboro drive over and back inside a day. A spring race means a cold grandstand and racing that is not. Ricky goes quiet for the last forty laps, which from him counts as excitement."
  },

  {
    date: "2027-04-25",
    kicker: "Talladega. April 25.",
    body: "Two and a half miles of Alabama, the whole field running in a knot, and a finish that has very little to do with driving. Ricky has a name for it that Sarah will not repeat. The spring one counts the same as the fall one, which is the part nobody cares for."
  },

  {
    date: "2027-05-23",
    kicker: "North Wilkesboro. May 23.",
    body: "An hour and fifteen up the road, which is close enough that nobody in this family watches this one on a television. Ricky ran that place when it was still a stop on the schedule, then watched it sit empty the better part of thirty years. It is the All-Star race this time and not the points race, and he will mention the difference more than once. Ella Mae has never liked racing and will be in the stands anyway."
  }

];

/* Shown once every dated entry above has passed. Keep it evergreen. */
window.TR_CALENDAR_OFFSEASON = {
  kicker: "Build season.",
  body: "Cold garage, warm tungsten, the '54 up on stands with more of it apart than together. This is the stretch where the truck actually gets worked on instead of talked about."
};
