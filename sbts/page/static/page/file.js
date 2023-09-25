let uploadfile = document.querySelector('#uploadfile');
let uploadbutton = document.querySelector('#uploadbutton');
let uploadform = document.querySelector('#uploadform');
let const_map = JSON.parse(document.querySelector('#file-data').text);
let url_map = const_map['url_map'];

uploadbutton.addEventListener('click', ev => {
    uploadfile.click();
});

uploadfile.addEventListener('change', ev => {
    if (uploadfile.files.length === 1) {
        uploadform.requestSubmit();
    }
});

uploadform.addEventListener('submit', async ev => {
    ev.preventDefault();

    let csrf_token = document.querySelector('[name=csrfmiddlewaretoken]').value;

    if (uploadfile.files.length !== 1) {
        return;
    }

    let file = uploadfile.files[0];

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
