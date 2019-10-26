#!/usr/local/bin/node

const { spawnSync } = require('child_process')
const { createWriteStream, existsSync, mkdirSync } = require('fs')
const { get } = require('https')
const { join } = require('path')
const { parse: queryParser } = require('querystring')
const { parse: urlParser } = require('url')

const { HOME } = process.env
const WALLPAPERS_DIR = `${HOME}/Google Drive/Pictures/Bing`
const DAYS_TO_RETAIN_WALLPAPERS = 365

mkdirSync(WALLPAPERS_DIR, { recursive: true })

const getBingIndexPage = url => {
  return new Promise((resolve, reject) => {
    const request = get(url, response => {
      let data = ''

      if (response.statusCode !== 200) {
        reject(new Error(`GET request failed with a ${response.statusCode}`))
      }

      response.on('data', chunk => data += chunk)
      response.on('end', () => resolve(data))
    })

    request.on('error', (err) => reject(err))
  })
}

const downloadAndSetWallpaperFromUrl = async urlObj => {
  const filename = queryParser(urlObj.query).id
    .replace(/^OHR./, '')
    .replace(/_EN-US[0-9]+/, '')
  const pathToFile = join(WALLPAPERS_DIR, filename)

  if (!existsSync(pathToFile)) {
    const file = createWriteStream(pathToFile)

    get(urlObj, response => {
      response.pipe(file)
      response.on('end', () => setDesktopPicture(pathToFile))
    })
  }
}

const setDesktopPicture = pathToFile => {
  const args = [
    '-e',
    `tell application "Finder" to set desktop picture to POSIX file "${pathToFile}"`,
    '>/dev/null',
    '2>&1',
  ]

  const options = {
    stdio: 'inherit',
  }

  spawnSync('/usr/bin/osascript', args, options)
}

const removeOldFiles = async () => {
  const args = [
    WALLPAPERS_DIR,
    '-name',
    '*.jpg',
    '-ctime',
    `+${DAYS_TO_RETAIN_WALLPAPERS}`,
    '-delete',
  ]

  const options = {
    stdio: 'inherit',
  }

  spawnSync('find', args, options)
}

const getWallpaperUrl = async url => {
  try {
    const data = await getBingIndexPage(url)
    const regex = /url:'(.*?)'/
    const path = regex.exec(data)[1]
    const downloadUrl = urlParser(path.replace(/^.*\//, url))

    return downloadUrl
  } catch (error) {
    console.error(error)
  }
}

;(async () => {
  const url = 'https://www.bing.com/'

  const wallpaperUrl = await getWallpaperUrl(url)
  await downloadAndSetWallpaperFromUrl(wallpaperUrl)
  await removeOldFiles()
})()
