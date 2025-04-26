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


export async function makeBackendCall(endpoint : string, requestMethod : string = "GET", body : any = null) : Promise<any> {
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

            // Parse response JSON if available
            const responseData = await response.json().catch(() => ({}));
            resolve(responseData);
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

export async function pollTaskStatus(taskId: string, onStatusUpdate: (status: string, result?: any) => void, 
                                    interval: number = 2000): Promise<any> {
    return new Promise((resolve, reject) => {
        const checkStatus = async () => {
            try {
                const taskData = await makeBackendCall(`corr/tasks/${taskId}/`);
                
                // Call the status update callback
                onStatusUpdate(taskData.status, taskData);
                
                // If task is completed or failed, resolve or reject
                if (taskData.status === 'COMPLETED') {
                    resolve(taskData);
                    return;
                } else if (taskData.status === 'FAILED') {
                    reject(taskData.error_message || 'Task failed');
                    return;
                }
                
                // Continue polling if not complete
                setTimeout(checkStatus, interval);
            } catch (error) {
                reject(error);
            }
        };
        
        // Start polling
        checkStatus();
    });
}
