// // Dylan Cease Pitch Tracker
// // Run with: node dylan_cease_pitches.js

// const DATE = "05/05/2026";
// const BASE = "https://statsapi.mlb.com/api/v1";
// const TARGET_PITCHER = "Shohei Ohtani";

// async function findCeasePitches() {
//   console.log(`\n📅 Fetching MLB schedule for ${DATE}...\n`);

//   const schedRes = await fetch(`${BASE}/schedule?sportId=1&date=${DATE}`);
//   const schedData = await schedRes.json();

//   const games = schedData.dates?.[0]?.games;
//   if (!games || games.length === 0) {
//     console.log("No games found for this date.");
//     return;
//   }

//   console.log(`Found ${games.length} game(s). Searching for ${TARGET_PITCHER}...\n`);

//   // Search all games for Dylan Cease
//   for (const game of games) {
//     const gameId = game.gamePk;
//     const matchup = `${game.teams.away.team.name} @ ${game.teams.home.team.name}`;

//     const pbpRes = await fetch(`${BASE}/game/${gameId}/playByPlay`);
//     const pbpData = await pbpRes.json();
//     const allPlays = pbpData.allPlays;

//     if (!allPlays || allPlays.length === 0) continue;

//     // Check if Dylan Cease pitched in this game
//     const ceasePlays = allPlays.filter(
//       play => play.matchup?.pitcher?.fullName === TARGET_PITCHER
//     );

//     if (ceasePlays.length === 0) continue;

//     // Found him
//     console.log(`✅ Found ${TARGET_PITCHER} in: ${matchup} (Game ID: ${gameId})`);
//     console.log(`   At-bats faced: ${ceasePlays.length}\n`);

//     // Pull game weather/conditions from game metadata
//     const gameRes = await fetch(`${BASE}/game/${gameId}/linescore`);
//     const gameData = await gameRes.json();

//     let totalPitches = 0;
//     let pitchSummary = { byType: {}, byResult: {} };

//     console.log(`${"=".repeat(70)}`);
//     console.log(`${TARGET_PITCHER} — Full Pitch Log`);
//     console.log(`${"=".repeat(70)}\n`);

//     for (const play of ceasePlays) {
//       const inning = play.about?.inning;
//       const half = play.about?.halfInning?.toUpperCase();
//       const batter = play.matchup?.batter?.fullName || "Unknown";
//       const result = play.result?.event || "Unknown";
//       const desc = play.result?.description || "";

//       console.log(`[${half} ${inning}] vs ${batter} → ${result}`);
//       console.log(`  ${desc}`);

//       const pitches = play.playEvents?.filter(e => e.isPitch) || [];

//       if (pitches.length === 0) {
//         console.log("  (no pitch data)\n");
//         continue;
//       }

//       pitches.forEach((pitch, i) => {
//         const pitchType = pitch.details?.type?.description || "Unknown";
//         const pitchCode = pitch.details?.code || "?";
//         const callDesc  = pitch.details?.description || "";
//         const speed     = pitch.pitchData?.startSpeed?.toFixed(1) || "N/A";
//         const zone      = pitch.pitchData?.zone ?? "N/A";
//         const spinRate  = pitch.pitchData?.breaks?.spinRate?.toFixed(0) || "N/A";
//         const pX        = pitch.pitchData?.coordinates?.pX?.toFixed(2) ?? "N/A";
//         const pZ        = pitch.pitchData?.coordinates?.pZ?.toFixed(2) ?? "N/A";
//         const breakV    = pitch.pitchData?.breaks?.breakVerticalInduced?.toFixed(1) ?? "N/A";
//         const breakH    = pitch.pitchData?.breaks?.breakHorizontal?.toFixed(1) ?? "N/A";
//         const balls     = pitch.count?.balls ?? "?";
//         const strikes   = pitch.count?.strikes ?? "?";
//         const isStrike  = pitch.details?.isStrike;
//         const isBall    = pitch.details?.isBall;
//         const isInPlay  = pitch.details?.isInPlay;

//         totalPitches++;

//         // Aggregate for summary
//         pitchSummary.byType[pitchType] = (pitchSummary.byType[pitchType] || 0) + 1;
//         pitchSummary.byResult[callDesc] = (pitchSummary.byResult[callDesc] || 0) + 1;

//         console.log(
//           `  Pitch ${String(i + 1).padStart(2)}: [${pitchCode}] ${pitchType.padEnd(22)} | ${callDesc.padEnd(20)} | ${speed} mph | Spin: ${spinRate} rpm | Zone: ${String(zone).padStart(2)} | pX: ${pX} pZ: ${pZ} | Break V: ${breakV}" H: ${breakH}" | Count: ${balls}-${strikes}`
//         );
//       });

//       console.log();
//     }

//     // Print summary
//     console.log(`${"=".repeat(70)}`);
//     console.log(`📊 ${TARGET_PITCHER} — Game Summary`);
//     console.log(`${"=".repeat(70)}`);
//     console.log(`Total pitches thrown: ${totalPitches}`);
//     console.log(`Total batters faced:  ${ceasePlays.length}\n`);

//     console.log("Pitch Mix:");
//     const sorted = Object.entries(pitchSummary.byType).sort((a, b) => b[1] - a[1]);
//     sorted.forEach(([type, count]) => {
//       const pct = ((count / totalPitches) * 100).toFixed(1);
//       const bar = "█".repeat(Math.round(pct / 3));
//       console.log(`  ${type.padEnd(25)} ${String(count).padStart(3)} pitches (${pct}%) ${bar}`);
//     });

//     console.log("\nOutcome Breakdown:");
//     const resultSorted = Object.entries(pitchSummary.byResult).sort((a, b) => b[1] - a[1]);
//     resultSorted.forEach(([result, count]) => {
//       const pct = ((count / totalPitches) * 100).toFixed(1);
//       console.log(`  ${result.padEnd(25)} ${String(count).padStart(3)} (${pct}%)`);
//     });

//     return; // Stop after finding Cease
//   }

//   console.log(`❌ ${TARGET_PITCHER} did not pitch on ${DATE}.`);
// }

// findCeasePitches();