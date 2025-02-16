<script lang="ts">
    interface Props {
        options : Array<any>
        unselectedText : any
        optionState : any
    }

    let { options, unselectedText, optionState: optionState = $bindable() } : Props = $props();
</script>



<select bind:value={optionState}>
    <option value="" selected disabled hidden> {unselectedText} </option>
    {#each options as option}
        <option value={option}>{option}</option>
    {/each}
</select>