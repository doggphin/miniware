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


export async function makeBackendCall(endpoint : string, setStatus : (status : StatusMessage) => void, requestMethod : string = "GET") {
    setStatus(StatusMessage.normalMessage("Thinking..."));

    let backendAddress = `${getBackendAddress()}/${endpoint}`;

    const response = await fetch(backendAddress, { method: requestMethod });
    const responseJson = await response.json();
    
    if(response.status == 200) {
        setStatus(StatusMessage.successMessage(responseJson["message"]));
    } else {
        setStatus(StatusMessage.errorMessage(responseJson["message"] ?? "Unknown error!"));
    }
}