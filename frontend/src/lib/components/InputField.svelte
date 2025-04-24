<script lang="ts">
    import TitledComponent from "./TitledComponent.svelte";

    interface Props {
        title : string,
        inputState : string,
        numericalOnly? : boolean,
        placeholderText? : string
    };

    let { 
        title, 
        inputState: inputState = $bindable(),
        numericalOnly = false,
        placeholderText = ""
    } : Props = $props();
    
    // Handle input validation for numerical-only fields
    function handleInput(event: Event) {
        if (numericalOnly) {
            const input = event.target as HTMLInputElement;
            const value = input.value;
            
            // Check if the input contains non-numerical characters (allow digits, decimal point, and minus sign)
            if (!/^-?\d*\.?\d*$/.test(value)) {
                // If invalid input, revert to the previous valid value by removing the last character
                input.value = value.slice(0, -1);
                // Update the bound value
                inputState = input.value;
            }
        }
    }
</script>


<TitledComponent title={title}>
    <input 
        class="bordered" 
        bind:value={inputState} 
        placeholder={placeholderText} 
        oninput={handleInput}
        type={numericalOnly ? "text" : "text"} 
    />
</TitledComponent>


<style>
    input {
        border-radius: var(--s4);
        padding: var(--s8);
        width: 100%;
    }
</style>
