let uploadform = document.querySelector('#uploadform');
let const_map = JSON.parse(document.querySelector('#file-data').text);
let url_map = const_map['url_map'];

uploadform.addEventListener('submit', async ev => {
    ev.preventDefault();

    let csrf_token = document.querySelector('[name=csrfmiddlewaretoken]').value;
    let file_elem = document.querySelector('#file');

    if (file_elem.files.length !== 1) {
        return;
    }

    let file = file_elem.files[0];

    try {
        let resp = await fetch(url_map['file:upload'], {
            method: 'POST',
            mode: 'same-origin',
            headers: {
                'Content-Type': 'application/octet-stream',
                'X-CSRFToken': csrf_token,
            },
            body: file,
        });

        if (!resp.ok) {
            throw new Error(await resp.text());
        }

        let {key} = await resp.json();
        document.querySelector('[name=blobkey]').value = key;
        document.querySelector('[name=filename]').value = file.name;
    } catch (e) {
        console.error(e);
    }

    uploadform.submit();
});
