import { StatusMessage } from "./statusMessage";


export function getBackendAddress() {
    return `http://${window.location.hostname}:8000`;
}


export function sanitizePartOfURI(endpoint : string) : string {
    console.log(endpoint);
    endpoint = endpoint.replace(/#/g, "%23");  // Replace hashtags with %23
    endpoint = endpoint.replace(/\//g, "%2F"); // Replace /s with %2F
    endpoint = endpoint.replace(/\\/g, "%5C"); // replace \s with %5C
    console.log(endpoint);
    return endpoint;
}


export async function makeBackendCall(endpoint : string, requestMethod : string = "GET", body : any = null) : Promise<void> {
    return new Promise(async(resolve, reject) => {
        let backendAddress = `${getBackendAddress()}/${endpoint}`;

        try {
            const response = await fetch(
                backendAddress, 
                { 
                    method: requestMethod,
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: body ? JSON.stringify(body) : null,
                });

            if(!response.ok) {
                const responseJson = await response.json().catch(() => ({})); // Prevent json parsing errors
                console.log(responseJson);
                reject(responseJson["message"] ?? "Unknown backend error!");
            }

            resolve();
        } catch (error) {
            if(error instanceof Error) {
                const humanReadableErrorMessages = new Map<String, string>([
                    ["Failed to fetch", `Could not reach backend server at ${getBackendAddress()}! Did you close it? Make sure to keep it open!`]
                ]);

                reject(humanReadableErrorMessages.get(error.message) ?? error.message);
            }

            reject(`Unknown error occured: ${error}`);
        }
    });
}
