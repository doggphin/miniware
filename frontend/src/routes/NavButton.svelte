<script lang="ts">
    interface Props {
        name : string
        url : string
    }

    let { name, url } : Props = $props();
</script>


<a href={`/${url}`}>
    {name}
</a>