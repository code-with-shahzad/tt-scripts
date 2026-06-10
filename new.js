const { TikTokLiveConnection } = require('tiktok-live-connector');
const readline = require('readline');

const SESSION_IDS = [
    "176fe741c87a89077d5551534638f7a4",
    "62c129a252218856386d6f1ed820b567",
    "df20a3975324769a20a8d993a369db79",
    "345f84c146f335afac10e3812e4c1036",
    "12f587f76da894ff4c97c377ef2d2701",
    "6b89789bec69edc6cc19f8339dee3a7c",
    "97070268205d331109684cc6ca65b05f",
    "765ffe2c064c2a12b79925e345d5ceaa",
    "aa0793fea02903d2a4175c9f3879a254",
    "a02c909d0d59748384b11876e3c95ff3",
    "a1f778c3ea389e24daa725ac77edd4ba",
    "7f645181d5936f3d04c4052f1dbd86c5",
    "7cc4ecf185702c25d84de8ce8e6ac03d",
    "ac92b3c19e435a2070e076b1d397af5f",
    "7cbd19de01ece28886d04b42d352a062",
    "a49e1e1fa53a86eedb0b2f32c61daac7",
    "c7f39c9046f21bf65cbb346dac2319a8",
    "d05154e0ce203af5551e09e75d415c60",
    "eb21f64a0864a803c4757ac9ebb45015",
    "e96ca45cbe375cc81ece8aac4b1a8511",
    "e3b4c90df76b91fb953368d7dda2d46e",
    "c37fd504e72356827cdca6de5ae02562",
    "e7873d8aa4512938f980226b966791b7",
    "ea3823f67daa95976dfcd68b56c21f8b",
    "f8fc5a7d71caefa8fa606eb0612ba21e",
    "ed5f8bd4d239ced09488d3986c400c29"
];

const WORDS = [
    "hacker is here", "Hacker is Here", "HACKER IS HERE",
    "you've been hacked", "You've Been Hacked",
    "hacker", "Hacker", "HACKER",
    "i'm in", "I'm in", "IM IN",
    "your account is mine", "Your Account Is Mine",
    "got you", "Got You", "GOT YOU",
];

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function getProxy() {
    // You can implement proxy fetching from proxies.txt here, 
    // similar to new.py. But for now we rely on tiktok-live-connector's connection options.
    return null;
}

function printStats(success, failed) {
    process.stdout.write(`\r[+] Comment - Success: ${success} | Failed: ${failed}`);
}

async function main() {
    rl.question('username : ', async (username) => {
        rl.close();

        username = username.trim().replace(/^@/, '');

        const signApiKey = process.env.SIGN_API_KEY;
        if (!signApiKey) {
            console.error("\n[!] Error: You need a valid Euler Stream API key to send messages.");
            console.error("Set it as an environment variable: export SIGN_API_KEY='your-api-key'");
            console.error("Get a key from https://www.eulerstream.com/ as documented in tiktok-live-connector.");
            process.exit(1);
        }

        console.log(`[*] Fetching live room information for @${username}...`);

        const connection = new TikTokLiveConnection(username, {
            signApiKey: signApiKey,
            authenticateWs: true
        });

        try {
            const state = await connection.connect();
            console.log(`[✓] User ID: ${state.roomInfo?.owner?.id || "unknown"}`);
            console.log(`[✓] Room ID: ${state.roomId}`);
            console.log("=".repeat(50));

            let commentSuccess = 0;
            let commentFailed = 0;
            let tasksLeft = 10000;
            let activeWorkers = 0;
            const maxWorkers = Math.min(30, SESSION_IDS.length);

            const startSpamWorker = async () => {
                activeWorkers++;
                while (tasksLeft > 0) {
                    tasksLeft--;

                    const sessionid = SESSION_IDS[Math.floor(Math.random() * SESSION_IDS.length)];
                    const word = WORDS[Math.floor(Math.random() * WORDS.length)];

                    try {
                        // Set the current session in the cookie jar
                        connection.webClient.cookieJar.setSession(sessionid, 'useast1a');

                        await connection.sendMessage(word);
                        commentSuccess++;
                        printStats(commentSuccess, commentFailed);
                    } catch (err) {
                        commentFailed++;
                        printStats(commentSuccess, commentFailed);
                        
                        // Print the first few errors to debug
                        if (commentFailed <= 3) {
                            console.error(`\n[!] Error details: ${err.message || err}`);
                            if (err.response && err.response.data) {
                                console.error(`[!] API Response: ${JSON.stringify(err.response.data)}`);
                            }
                        }
                    }

                    // Random sleep equivalent to python's random.uniform(1.0, 3.0)
                    await delay(Math.random() * 2000 + 1000);
                }
                activeWorkers--;
            };

            const promises = [];
            for (let i = 0; i < maxWorkers; i++) {
                promises.push(startSpamWorker());
                // Small stagger between starting workers
                await delay(100);
            }

            await Promise.all(promises);

            console.log("\n" + "=".repeat(50));
            console.log(`[✓] Final - Success: ${commentSuccess} | Failed: ${commentFailed}`);
            process.exit(0);

        } catch (err) {
            console.error(`\n[!] Error connecting: ${err.message || err}`);
            process.exit(1);
        }
    });
}

main();
